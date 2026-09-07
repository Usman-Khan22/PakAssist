import { copy, type LocalizedText } from "../translations";
import { useLanguage, authoredText } from "../language";
import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ArrowRight, ClipboardCheck, FileText, Search, Sparkles } from "lucide-react";
import LanguageSwitcher from "../components/LanguageSwitcher";
import Logo from "../components/Logo";
import Button from "../components/Button";
import Header from "../components/Header";
import AssistantResponse from "../components/AssistantResponse";

type ChatMsg = { from: "user" | "assistant"; text: string | LocalizedText };

export default function Chat() {
  const { t, localize } = useLanguage();
  const [params] = useSearchParams();
  const query = params.get("query");
  const initial = query ? authoredText(query) : null;
  const [messages, setMessages] = useState<ChatMsg[]>(
    initial
      ? [
          { from: "user", text: initial },
          {
            from: "assistant",
            text: copy.hereIsAClearStartingPointForYourQuestion,
          },
        ]
      : [
          {
            from: "user",
            text: copy.whatDocumentsDoINeedToRenewMyPassport,
          },
          {
            from: "assistant",
            text: copy.forAPassportRenewalYoullGenerallyNeedTheseItems,
          },
        ],
  );
  const [input, setInput] = useState("");
  const [title, setTitle] = useState<string | LocalizedText>(initial || copy.passportRenewal);
  const send = (text: string | LocalizedText = input.trim()) => {
    if (!text) return;
    setMessages([
      ...messages,
      { from: "user", text },
      {
        from: "assistant",
        text: copy.hereIsAPracticalGuideBasedOnTheInformation,
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
              setTitle(copy.newConversation);
            }}
          > {t.newChat} </Button>
          <div className="sidebar-search">
            <Search size={15} /> {t.searchChats} </div>
          <small> {t.pinnedTopics} </small>
          <Link to="/services/passport-renewal">
            <FileText size={15} /> {t.passportRenewal2} </Link>
          <Link to="/services/cnic-renewal">
            <ClipboardCheck size={15} /> {t.cnicRenewal2} </Link>
          <small> {t.recentChats} </small>
          <span className="chat-date"> {t.today} </span>
          <button className="chat-history active"> {t.passportRenewal} </button>
          <button className="chat-history"> {t.fbrTaxFilerGuide} </button>
          <span className="chat-date"> {t.yesterday} </span>
          <button className="chat-history"> {t.learnerPermitRequirements} </button>
        </aside>
        <section className="chat-main">
          <div className="chat-toolbar">
            <div>
              <span className="online-dot" /> <b>{localize(title)}</b>
              <small> {t.aiAgentActive} </small>
            </div>
            <LanguageSwitcher />
          </div>
          <div className="message-thread">
            {messages.length === 0 ? (
              <div className="chat-empty">
                <Sparkles size={30} />
                <h2> {t.whatCanWeHelpYouNavigate} </h2>
                <p> {t.askAboutAGovernmentServiceInPlainLanguage} </p>
              </div>
            ) : (
              messages.map((m, i) => (
                <div className={`message ${m.from}`} key={i}>
                  {m.from === "assistant" && <span className="avatar">P</span>}
                  <div className="bubble">
                    <p>{localize(m.text)}</p>
                    {m.from === "assistant" && <AssistantResponse />}
                  </div>
                </div>
              ))
            )}
            {messages.length > 0 && (
              <div className="followups">
                <span> {t.continueWith} </span>
                {[
                  copy.normalOrUrgent,
                  copy.adultOrMinor,
                  copy.islamabadOrOtherCity,
                ].map((x) => (
                  <button key={x.en} onClick={() => send(x)}>
                    {localize(x)}
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
              placeholder={t.askAFollowupQuestion}
            />
            <span> {t.attachmentsComingSoon} </span>
            <button aria-label={t.sendMessage}>
              <ArrowRight />
            </button>
          </form>
        </section>
      </main>
    </>
  );
}
