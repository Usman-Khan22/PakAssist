import { default as ReactMarkdown } from 'react-markdown';
import { default as remarkGfm } from 'remark-gfm';

export function AssistantMarkdown({ text }: { text: string }) {
  return (
    <div className="markdown-response" dir="auto">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ node: _node, ...props }) => (
            <a {...props} target="_blank" rel="noreferrer noopener" />
          ),
        }}
      >
        {text}
      </ReactMarkdown>
    </div>
  );
}
