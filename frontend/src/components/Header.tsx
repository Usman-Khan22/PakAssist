import { copy } from "../translations";
import { useLanguage } from "../language";
import { useEffect, useRef, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { Menu, X } from "lucide-react";
import LanguageSwitcher from "./LanguageSwitcher";

const navItems = [
  [copy.services, "/services"],
  [copy.howItWorks, "/how-it-works"],
  [copy.officialSources, "/#sources"],
  [copy.about, "/about"],
] as const;

export default function Header() {
  const { t, localize } = useLanguage();
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const toggle = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    setOpen(false);
    if (location.pathname === "/" && location.hash === "#sources") {
      document.getElementById("sources")?.scrollIntoView();
    }
  }, [location]);
  return (
    <header className={`site-header${open ? " menu-open" : ""}`} onKeyDown={(event) => {
      if (event.key === "Escape" && open) {
        setOpen(false);
        toggle.current?.focus();
      }
    }}>
      <div className="container header-inner">
        <Link to="/" className="brand ltr-isolate" lang="en">PakAssist</Link>
        <nav id="primary-navigation" className="desktop-nav" aria-label={t.mainNavigation}>
          {navItems.map(([label, path]) => (
            path.includes("#") ? <Link key={path} to={path} onClick={() => {
              setOpen(false);
              if (location.pathname === "/") document.getElementById("sources")?.scrollIntoView();
            }}>{localize(label)}</Link> : <NavLink key={path} to={path} onClick={() => setOpen(false)}>
              {localize(label)}
            </NavLink>
          ))}
        </nav>
        <div className="header-actions">
          <LanguageSwitcher />
          <Link className="primary-button" to="/chat" onClick={() => setOpen(false)}> {t.askPakassist} </Link>
          <button
            ref={toggle}
            type="button"
            className="header-menu-toggle"
            aria-label={localize(open ? copy.closeNavigation : copy.openNavigation)}
            aria-expanded={open}
            aria-controls="primary-navigation"
            onClick={() => setOpen(!open)}
          >
            {open ? <X /> : <Menu />}
          </button>
        </div>
      </div>
    </header>
  );
}
