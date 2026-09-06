import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ArrowRight, ClipboardCheck, FileText, Globe2, Search, Sparkles } from "lucide-react";
import Logo from "../components/Logo";
import Button from "../components/Button";
import Header from "../components/Header";
import AssistantResponse from "../components/AssistantResponse";

type ChatMsg = { from: "user" | "assistant"; text: string };

export default function Chat() {
  const [params] = useSearchParams();
  const initial = params.get("query");
  const [messages, setMessages] = useState<ChatMsg[]>(
    initial
      ? [
          { from: "user", text: initial },
          {
            from: "assistant",
            text: "Here is a clear starting point for your question.",
          },
        ]
      : [
          {
            from: "user",
            text: "What documents do I need to renew my passport?",
          },
          {
            from: "assistant",
            text: "For a passport renewal, you’ll generally need these items ready:",
          },
        ],
  );
  const [input, setInput] = useState("");
  const [title, setTitle] = useState(initial || "Passport Renewal");
  const send = (text = input.trim()) => {
    if (!text) return;
    setMessages([
      ...messages,
      { from: "user", text },
      {
        from: "assistant",
        text: "Here is a practical guide based on the information available. I’ll keep the next steps clear and actionable.",
      },
    ]);
    setTitle(text);
    setInput("");
  };
  return (
    <>
      <Header />
      <main className="chat-page">
        <aside className="chat-sidebar">
          <Logo />
          <Button
            onClick={() => {
              setMessages([]);
              setTitle("New conversation");
            }}
          >
            New chat
          </Button>
          <div className="sidebar-search">
            <Search size={15} /> Search chats
          </div>
          <small>PINNED TOPICS</small>
          <Link to="/services/passport-renewal">
            <FileText size={15} /> Passport renewal
          </Link>
          <Link to="/services/cnic-renewal">
            <ClipboardCheck size={15} /> CNIC renewal
          </Link>
          <small>RECENT CHATS</small>
          <span className="chat-date">TODAY</span>
          <button className="chat-history active">Passport Renewal</button>
          <button className="chat-history">FBR tax filer guide</button>
          <span className="chat-date">YESTERDAY</span>
          <button className="chat-history">Learner permit requirements</button>
        </aside>
        <section className="chat-main">
          <div className="chat-toolbar">
            <div>
              <span className="online-dot" /> <b>{title}</b>
              <small>AI Agent Active</small>
            </div>
            <button className="language">
              <Globe2 size={14} /> EN / اردو
            </button>
          </div>
          <div className="message-thread">
            {messages.length === 0 ? (
              <div className="chat-empty">
                <Sparkles size={30} />
                <h2>What can we help you navigate?</h2>
                <p>Ask about a government service in plain language.</p>
              </div>
            ) : (
              messages.map((m, i) => (
                <div className={`message ${m.from}`} key={`${m.text}-${i}`}>
                  {m.from === "assistant" && <span className="avatar">P</span>}
                  <div className="bubble">
                    <p>{m.text}</p>
                    {m.from === "assistant" && <AssistantResponse />}
                  </div>
                </div>
              ))
            )}
            {messages.length > 0 && (
              <div className="followups">
                <span>Continue with</span>
                {[
                  "Normal or Urgent?",
                  "Adult or Minor?",
                  "Islamabad or Other City?",
                ].map((x) => (
                  <button key={x} onClick={() => send(x)}>
                    {x}
                    <ArrowRight size={13} />
                  </button>
                ))}
              </div>
            )}
          </div>
          <form
            className="chat-input"
            onSubmit={(e) => {
              e.preventDefault();
              send();
            }}
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a follow-up question..."
            />
            <span>Attachments coming soon</span>
            <button aria-label="Send message">
              <ArrowRight />
            </button>
          </form>
        </section>
      </main>
    </>
  );
}
