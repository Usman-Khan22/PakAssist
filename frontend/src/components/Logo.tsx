import { Link } from "react-router-dom";

export default function Logo({ footer = false }: { footer?: boolean }) {
  return (
    <Link to="/" className="logo">
      <span className="logo-tile">
        <span />
      </span>
      <b>
        Pak<span className={footer ? "gold" : ""}>Assist</span>
      </b>
    </Link>
  );
}
