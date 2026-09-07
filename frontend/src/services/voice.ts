export const makeVoiceFriendly = (text: string) => {
  const cleaned = text
    .replace(/#{1,6}\s*/g, "")
    .replace(/\*\*/g, "")
    .replace(/\*/g, "")
    .replace(/□/g, "")
    .trim();

  // Extract bullet points
  const bullets = cleaned
    .split("\n")
    .map((line) =>
      line
        .replace(/^\s*[-•]\s*/, "")
        .trim()
    )
    .filter(
      (line) =>
        line.length > 0 &&
        !line.toLowerCase().startsWith("required documents") &&
        !line.toLowerCase().startsWith("note:")
    );

  // If answer looks like a document/checklist response
  if (
    cleaned.toLowerCase().includes("required documents") &&
    bullets.length > 0
  ) {
    const usefulItems = bullets
      .slice(0, 5)
      .map((item) =>
        item
          .replace(/\.$/, "")
          .replace(/\([^)]{80,}\)/g, "")
          .trim()
      );

    if (usefulItems.length === 1) {
      return `You will need ${usefulItems[0]}.`;
    }

    const lastItem = usefulItems.pop();

    return (
      `For this, you will need ${usefulItems.join(", ")}, ` +
      `and ${lastItem}. Please confirm the final requirements for your province.`
    );
  }

  // Generic fallback for non-list answers
  const plainText = cleaned
    .replace(/\n+/g, " ")
    .replace(/\s+/g, " ")
    .trim();

  const sentences =
    plainText.match(/[^.!?]+[.!?]+/g) || [];

  if (sentences.length > 0) {
    const summary = sentences
      .slice(0, 2)
      .join(" ")
      .trim();

    return summary;
  }

  return plainText.length > 350
    ? plainText.slice(0, 350) + "."
    : plainText;
};

