export const MAX_SPOKEN_CHARACTERS = 500;

const detailLabel = /(?:address|pata|phone(?:\s+number)?|telephone|contact(?:\s+(?:details|number))?|services?|(?:opening\s+)?hours|auqaat|portal|confidence(?:\s+notes?)?|bharosa|sources?|references?|citations?|notes?|پتہ|فون|سروسز?|اوقات|پورٹل|اعتماد|ماخذ|حوالہ جات|حوالے|نوٹ)\s*[:：]/iu;
const sourceHeading = /^(?:sources?|references?|citations?|ماخذ|حوالہ جات|حوالے)\s*[:：]?$/iu;
const listPrefix = /^\s*(?:[-*•▪□☐✓✔]\s*|\d+[.)]\s+|\[[ xX]\]\s*)/u;
const sentenceEnd = /[.!?۔؟]$/u;

const detailsReminder = (text: string) => {
  if (/[\u0600-\u06ff]/u.test(text)) return 'پوری تفصیل چیٹ میں دیکھ لیں۔';
  if (/\b(?:aap|apko|mujhe|mein|hain|hai|chahiye|karein|liye|nahin|yeh)\b/iu.test(text)) {
    return 'Poori tafseel chat mein dekh lein.';
  }
  return 'Full details are shown in the chat.';
};

/** Extract a short spoken preview; the original answer stays visible in chat. */
export const makeVoiceFriendly = (text: string): string => {
  if (!text.trim()) return '';

  const reminder = detailsReminder(text);
  const contentLimit = MAX_SPOKEN_CHARACTERS - reminder.length - 1;
  const lines: string[] = [];
  let shortened = false;
  let listItems = 0;
  let inSources = false;

  for (const rawLine of text.replace(/```[\s\S]*?```/g, '').split(/\r?\n/u)) {
    const isListItem = listPrefix.test(rawLine.trim());
    let line = rawLine
      .replace(/^\s*#{1,6}\s*/u, '')
      .replace(listPrefix, '')
      .replace(/^\[[ xX]\]\s*/u, '')
      .replace(/\[([^\]]+)\]\([^)]*\)/gu, '$1')
      .replace(/[*_`]/g, '')
      .trim();
    if (!line) continue;

    // Service-center fields are localized by the backend. Do not read out
    // entire addresses, contact numbers, confidence metadata or source lists.
    if (sourceHeading.test(line)) inSources = true;
    if (inSources || line.includes('|') || /^\[\d+\]:/u.test(line)) {
      shortened = true;
      continue;
    }
    const field = detailLabel.exec(line);
    if (field && (field.index === 0 || /[\s;,.(]$/u.test(line.slice(0, field.index)))) {
      line = line.slice(0, field.index).trim();
      shortened = true;
    }
    const withoutContacts = line
      .replace(/(?:https?:\/\/|www\.)\S+/giu, '')
      .replace(/\+?\d[\d ()-]{8,}\d/gu, (number) =>
        number.replace(/\D/g, '').length >= 10 ? '' : number)
      .replace(/\[\d+\]/gu, '')
      .replace(/\s+/gu, ' ')
      .trim();
    if (withoutContacts !== line) shortened = true;
    line = withoutContacts;
    if (!line) continue;

    if (isListItem && ++listItems > 3) {
      shortened = true;
      continue;
    }
    // Joining short list entries with semicolons keeps a heading and a few
    // useful examples together without turning the full checklist into speech.
    if (isListItem) line = line.replace(/[.!?۔؟]+$/u, '') + ';';
    else if (!sentenceEnd.test(line) && !/[:：]$/u.test(line)) line += '.';
    lines.push(line);
  }

  const plainText = lines.join(' ').replace(/;(?=\s*$)/u, '.').trim();
  // A decimal or an initial inside a name is not a sentence boundary.
  const sentences = plainText.match(/.+?(?:[.!?۔؟]+(?=\s|$)|$)/gu) ?? [];
  let summary = sentences.slice(0, 2).join('').trim();
  if (sentences.length > 2) shortened = true;

  if (summary.length > contentLimit) {
    // Prefer a whole sentence; when the first sentence itself is long, cut at
    // a word boundary and leave room for the reminder instead of reading it all.
    const firstSentence = sentences[0]?.trim() ?? '';
    if (firstSentence.length <= contentLimit) summary = firstSentence;
    else {
      const clipped = summary.slice(0, contentLimit - 1);
      const lastSpace = clipped.lastIndexOf(' ');
      summary = (lastSpace > 0 ? clipped.slice(0, lastSpace) : '').replace(/[;,:：]+$/u, '').trim();
      if (summary) summary += '…';
    }
    shortened = true;
  }

  if (!summary) return reminder;
  if (!sentenceEnd.test(summary) && !summary.endsWith('…')) summary = summary.replace(/[;,:：]+$/u, '') + '.';
  return shortened ? `${summary} ${reminder}` : summary;
};

