import { Link } from "react-router-dom";
import Logo from "./Logo";

export default function Footer() {
  return (
    <footer>
      <div className="footer-grid">
        <div>
          <Logo footer />
          <p className="footer-tag">
            Making civic services simple,
            <br />
            one question at a time.
          </p>
        </div>
        <div>
          <small>EXPLORE</small>
          <Link to="/services">All Services</Link>
          <Link to="/chat">Ask PakAssist</Link>
          <Link to="/how-it-works">How it works</Link>
        </div>
        <div>
          <small>COMPANY</small>
          <Link to="/about">About us</Link>
          <a href="#trust">Trust & safety</a>
          <a href="#contact">Contact</a>
        </div>
        <div className="footer-note">
          <small>IMPORTANT</small>
          <p>
            PakAssist is an independent civic-tech guide. Always verify final
            details on official .gov.pk portals.
          </p>
        </div>
      </div>
      <div className="footer-bottom">
        <span>© 2025 PakAssist. Built by citizens, for citizens.</span>
        <span>Terms&nbsp;&nbsp; Privacy&nbsp;&nbsp; Security</span>
      </div>
    </footer>
  );
}
