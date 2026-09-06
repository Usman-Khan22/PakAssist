import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { ArrowRight, CircleHelp, Menu, X } from "lucide-react";
import Logo from "./Logo";
import LanguageSwitcher from "./LanguageSwitcher";

const navItems = [
  ["Home", "/"],
  ["Services", "/services"],
  ["How It Works", "/how-it-works"],
  ["About", "/about"],
];

export default function Header() {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();
  return (
    <header className="site-header">
      <div className="nav-wrap">
        <Logo />
        <nav className={open ? "nav-open" : ""}>
          {navItems.map(([label, path]) => (
            <NavLink key={path} to={path} onClick={() => setOpen(false)}>
              {label}
            </NavLink>
          ))}
          <button className="nav-ask" onClick={() => navigate("/chat")}>
            Ask PakAssist <ArrowRight size={15} />
          </button>
        </nav>
        <div className="nav-tools">
          <LanguageSwitcher />
          <button className="access" aria-label="Accessibility options">
            <CircleHelp size={19} />
          </button>
          <button
            className="mobile-menu"
            aria-label="Toggle menu"
            onClick={() => setOpen(!open)}
          >
            {open ? <X /> : <Menu />}
          </button>
        </div>
      </div>
    </header>
  );
}
