import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Mic, Search } from "lucide-react";

const suggestions = [
  "Renew CNIC online",
  "Passport document checklist",
  "International driving permit",
  "FBR tax filer guide",
];

export default function HeroSearch({ urdu = false }: { urdu?: boolean }) {
  const prompt = urdu
    ? "آپ کس سرکاری خدمت کے بارے میں جاننا چاہتے ہیں؟"
    : "Ask about any government service...";
  const [text, setText] = useState("");
  const navigate = useNavigate();
  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    navigate(`/chat${text ? `?query=${encodeURIComponent(text)}` : ""}`);
  };
  return (
    <>
      <form className="hero-search" onSubmit={submit}>
        <Search size={19} />
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={prompt}
          aria-label={prompt}
          data-localized
        />
        <button
          className="voice-search"
          type="button"
          disabled
          aria-label="Voice search coming soon"
          title="Voice search coming soon"
        >
          <Mic size={18} />
        </button>
        <button aria-label="Search">
          <ArrowRight />
        </button>
      </form>
      <div className="chips">
        {suggestions.map((x) => (
          <button
            key={x}
            onClick={() => navigate(`/chat?query=${encodeURIComponent(x)}`)}
          >
            {x}
          </button>
        ))}
      </div>
    </>
  );
}
