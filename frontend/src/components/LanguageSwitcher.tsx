import { useEffect, useState } from "react";
import { getStoredLanguage, setStoredLanguage } from "../language";

export default function LanguageSwitcher() {
  const [urdu, setUrdu] = useState(getStoredLanguage);
  useEffect(() => {
    setStoredLanguage(urdu);
  }, [urdu]);
  return (
<button
            type="button"
            className="language language-switcher"
            onClick={() => setUrdu(!urdu)}
            aria-label={urdu ? "Switch to English" : "اردو میں تبدیل کریں"}
            lang={urdu ? "en" : "ur"}
            dir={urdu ? "ltr" : "rtl"}
          >
            {urdu ? "English" : "اردو"}
          </button>
  );
}
