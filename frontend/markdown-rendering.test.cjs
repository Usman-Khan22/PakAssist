const { test, after } = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');

let vite;

after(async () => {
  await vite?.close();
});

async function renderMarkdown(text) {
  if (!vite) {
    const { createServer } = await import('vite');
    vite = await createServer({
      root: __dirname,
      server: { middlewareMode: true },
      appType: 'custom',
      logLevel: 'silent',
    });
  }
  const { AssistantMarkdown } = await vite.ssrLoadModule('/src/components/AssistantMarkdown.tsx');
  return renderToStaticMarkup(React.createElement(AssistantMarkdown, { text }));
}

test('assistant Markdown renders headings, checklist lines, bold text and safe links', async () => {
  const text = [
    'Here is the **checklist**...',
    '',
    '### Adults (18 and above)',
    '',
    '☐ Original CNIC',
    '☐ Previous passport',
    '',
    '### Minors (under 18)',
    '',
    '- ☐ CRC / Form B',
    '- ☐ Parent or **guardian**',
    '',
    '[Official guidance](https://example.gov.pk/passport)',
  ].join('\n');
  const html = await renderMarkdown(text);
  assert.match(html, /<h3>Adults \(18 and above\)<\/h3>/);
  assert.match(html, /<h3>Minors \(under 18\)<\/h3>/);
  assert.doesNotMatch(html, /###/);
  assert.match(html, /<strong>checklist<\/strong>/);
  assert.match(html, /<strong>guardian<\/strong>/);
  assert.match(html, /<ul>/);
  assert.match(html, /☐ Original CNIC/);
  assert.match(html, /href="https:\/\/example\.gov\.pk\/passport"/);
  assert.match(html, /target="_blank"/);
  assert.match(html, /rel="noreferrer noopener"/);
});

test('assistant Markdown does not execute raw HTML or unsafe link protocols', async () => {
  const html = await renderMarkdown('<img src=x onerror="alert(1)"> [bad](javascript:alert(1))');
  assert.doesNotMatch(html, /<img/);
  assert.match(html, /&lt;img src=x onerror=/);
  assert.doesNotMatch(html, /href="javascript:/);
});
