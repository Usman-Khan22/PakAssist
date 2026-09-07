import { setStoredLanguage, useLanguage } from '../language';
import { copy } from '../translations';
export default function LanguageSwitcher() {
  const { language } = useLanguage();
  const urdu = language === 'ur';
  return <button type="button" className="language language-switcher"
    onClick={() => setStoredLanguage(!urdu)}
    aria-label={urdu ? copy.switchLanguage.en : copy.switchLanguage.ur}
    lang={urdu ? 'en' : 'ur'} dir={urdu ? 'ltr' : 'rtl'}>
    {urdu ? copy.languageName.en : copy.languageName.ur}
  </button>;
}
