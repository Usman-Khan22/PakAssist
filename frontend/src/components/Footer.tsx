import { useLanguage } from "../language";
import { Link } from "react-router-dom";
import Logo from "./Logo";

export default function Footer() {
  const { t } = useLanguage();
  return (
    <footer>
      <div className="footer-grid">
        <div>
          <Logo footer />
          <p className="footer-tag"> {t.makingCivicServicesSimple} <br /> {t.oneQuestionAtATime} </p>
        </div>
        <div>
          <small> {t.explore} </small>
          <Link to="/services"> {t.allServices} </Link>
          <Link to="/chat"> {t.askPakassist} </Link>
          <Link to="/how-it-works"> {t.howItWorks} </Link>
        </div>
        <div>
          <small> {t.company} </small>
          <Link to="/about"> {t.aboutUs} </Link>
          <a href="/#sources"> {t.trustSafety} </a>
          <a href="#contact"> {t.contact} </a>
        </div>
        <div className="footer-note">
          <small> {t.important} </small>
          <p> {t.pakassistIsAnIndependentCivictechGuideAlwaysVerifyFinal} </p>
        </div>
      </div>
      <div className="footer-bottom">
        <span> {t.value2025PakassistBuiltByCitizensForCitizens} </span>
        <span>{t.termsprivacysecurity}</span>
      </div>
    </footer>
  );
}
