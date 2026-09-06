import { useId, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Mic, Search } from "lucide-react";
import { services } from "../data";

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
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const listId = useId();
  const query = text.trim().toLowerCase();
  const matches = query ? services.filter(service => service.title.toLowerCase().includes(query)).slice(0, 6) : [];
  const expanded = open && query.length > 0;
  const navigate = useNavigate();
  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (expanded && active >= 0 && matches[active]) {
      navigate(`/services/${matches[active].slug}`);
      setOpen(false);
      return;
    }
    navigate(`/chat${text ? `?query=${encodeURIComponent(text)}` : ""}`);
  };
  return (
    <>
      <div className="hero-search-wrapper" onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false);
      }}>
      <form className="hero-search" role="search" onSubmit={submit}>
        <Search size={19} />
        <input
          value={text}
          onChange={(e) => { setText(e.target.value); setActive(-1); setOpen(true); }}
          onFocus={() => setOpen(true)}
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={expanded}
          aria-controls={expanded ? listId : undefined}
          aria-activedescendant={expanded && active >= 0 ? `${listId}-${active}` : undefined}
          autoComplete="off"
          onKeyDown={(event) => {
            if (event.nativeEvent.isComposing) return;
            if (event.key === "Escape") {
              event.preventDefault();
              setOpen(false);
              setActive(-1);
            } else if (event.key === "ArrowDown" || event.key === "ArrowUp") {
              event.preventDefault();
              setOpen(true);
              if (matches.length) setActive(previous => {
                const next = event.key === "ArrowDown"
                  ? (!expanded ? 0 : (previous + 1) % matches.length)
                  : (!expanded || previous <= 0 ? matches.length - 1 : previous - 1);
                requestAnimationFrame(() => document.getElementById(`${listId}-${next}`)?.scrollIntoView({ block: "nearest" }));
                return next;
              });
            }
          }}
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
      {expanded && (
        <div className="search-suggestions" data-localized>
          <ul id={listId} role="listbox" aria-label={urdu ? "خدمات کی تجاویز" : "Suggested services"}>
            {matches.map((service, index) => (
              <li key={service.slug} id={`${listId}-${index}`} role="option" aria-selected={active === index}
                onPointerDown={(event) => event.preventDefault()}
                onClick={() => { setOpen(false); navigate(`/services/${service.slug}`); }}>
                <bdi lang="en">{service.title}</bdi>
                <small><bdi lang="en">{service.authority} · {service.category}</bdi></small>
              </li>
            ))}
          </ul>
          {!matches.length && <p role="status">{urdu ? "کوئی متعلقہ خدمت نہیں ملی۔ پاک اسسٹ سے پوچھنے کے لیے انٹر دبائیں۔" : "No matching service found. Press Enter to ask PakAssist."}</p>}
        </div>
      )}
      </div>
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
