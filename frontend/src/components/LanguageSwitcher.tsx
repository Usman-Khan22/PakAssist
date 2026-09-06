import { useEffect, useState } from "react";
import { ChevronDown, Globe2 } from "lucide-react";
import { getStoredLanguage, setStoredLanguage } from "../language";

export default function LanguageSwitcher() {
  const [urdu, setUrdu] = useState(getStoredLanguage);
  useEffect(() => {
    setStoredLanguage(urdu);
  }, [urdu]);
  return (
<button
            className="language"
            onClick={() => setUrdu(!urdu)}
            aria-label="Switch language"
          >
            <Globe2 size={15} />
            <span>{urdu ? "اردو" : "EN"}</span>
            <ChevronDown size={13} />
          </button>
  );
}
