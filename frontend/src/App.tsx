import { useEffect, useState } from "react";
import {
  Link,
  NavLink,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import {
  ArrowRight,
  BookOpen,
  CalendarDays,
  Check,
  ChevronDown,
  ChevronRight,
  CircleHelp,
  ClipboardCheck,
  CreditCard,
  FileText,
  Gauge,
  Globe2,
  Landmark,
  Menu,
  Mic,
  Search,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";
import { categories, getService, services, type Service } from "./data";
import { getServiceBySlug, getServices } from "./services/api";
import { getStoredLanguage, setStoredLanguage } from "./language";

const suggestions = [
  "Renew CNIC online",
  "Passport document checklist",
  "International driving permit",
  "FBR tax filer guide",
];
const navItems = [
  ["Home", "/"],
  ["Services", "/services"],
  ["How It Works", "/how-it-works"],
  ["About", "/about"],
];
function Logo({ footer = false }: { footer?: boolean }) {
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
function Button({
  children,
  variant = "primary",
  onClick,
  icon = true,
  type = "button",
}: {
  children: React.ReactNode;
  variant?: "primary" | "outline" | "quiet";
  onClick?: () => void;
  icon?: boolean;
  type?: "button" | "submit";
}) {
  return (
    <button type={type} onClick={onClick} className={`btn btn-${variant}`}>
      {children}
      {icon && <ArrowRight size={16} />}
    </button>
  );
}
function Header() {
  const [open, setOpen] = useState(false);
  const [urdu, setUrdu] = useState(getStoredLanguage);
  const navigate = useNavigate();
  useEffect(() => {
    setStoredLanguage(urdu);
  }, [urdu]);
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
          <button
            className="language"
            onClick={() => setUrdu(!urdu)}
            aria-label="Switch language"
          >
            <Globe2 size={15} />
            <span>{urdu ? "اردو" : "EN"}</span>
            <ChevronDown size={13} />
          </button>
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
function Footer() {
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
function SectionHeader({
  overline,
  title,
  description,
}: {
  overline: string;
  title: string;
  description?: string;
}) {
  return (
    <div className="section-head">
      <small>{overline}</small>
      <h2>{title}</h2>
      <div className="diamonds">
        <i />
        <i />
        <i />
      </div>
      {description && <p>{description}</p>}
    </div>
  );
}
function HeroSearch() {
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
          placeholder="Ask about any government service..."
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
function ResponsePreview() {
  return (
    <div className="response-preview">
      <div className="response-top">
        <span className="verified">
          <ShieldCheck size={15} /> Verified guidance
        </span>
        <span>Just now</span>
      </div>
      <p className="question">“What documents do I need to renew my CNIC?”</p>
      <div className="assistant-line">
        <span className="avatar">P</span>
        <p>
          You’ll need your original CNIC and a recent photograph. Here’s the
          complete checklist:
        </p>
      </div>
      <div className="mini-checks">
        {[
          "Original CNIC",
          "Recent photograph",
          "Proof of address",
          "Fee payment receipt",
        ].map((x) => (
          <div key={x}>
            <Check size={15} />
            {x}
          </div>
        ))}
      </div>
      <div className="info-strip">
        <span>i</span> Requirements can vary by case. Verify at nadra.gov.pk
      </div>
    </div>
  );
}
function Stats() {
  return (
    <div className="stats">
      <div>
        <b>
          50,000<span>+</span>
        </b>
        <small>Citizens Guided</small>
      </div>
      <div>
        <b>
          200<span>+</span>
        </b>
        <small>Services Cataloged</small>
      </div>
      <div>
        <b>24/7</b>
        <small>Instant Availability</small>
      </div>
      <div>
        <b>
          EN <span>اردو</span>
        </b>
        <small>Bilingual Support</small>
      </div>
    </div>
  );
}
const categoryData = [
  [
    "Passport Services",
    "Your passport journey, clearly explained.",
    "Passport",
  ],
  ["CNIC / NADRA", "Identity services without the confusion.", "CNIC/NADRA"],
  ["Driving License", "From learner permit to renewal.", "Driving License"],
  [
    "Vehicle Registration",
    "Transfer, tax and registration guidance.",
    "Vehicle Registration",
  ],
  [
    "Tax & FBR Assistance",
    "Understand filing without the jargon.",
    "Tax & Revenue",
  ],
  [
    "Domicile & Certificates",
    "The documents your next step needs.",
    "Documents",
  ],
];
function CategoryCard({ item }: { item: string[] }) {
  const navigate = useNavigate();
  const icons: Record<string, typeof FileText> = {
    Passport: BookOpen,
    "CNIC/NADRA": CreditCard,
    "Driving License": CalendarDays,
    "Vehicle Registration": FileText,
    "Tax & Revenue": ShieldCheck,
    Documents: Landmark,
  };
  const Icon = icons[item[2]] || FileText;
  return (
    <button
      className="category-card"
      onClick={() =>
        navigate(`/services?category=${encodeURIComponent(item[2])}`)
      }
    >
      <span className="icon-tile">
        <Icon size={19} />
      </span>
      <span>
        <b>{item[0]}</b>
        <small>{item[1]}</small>
      </span>
      <ArrowRight size={17} />
    </button>
  );
}
function Stepper({
  steps = [
    "Eligibility",
    "Documents",
    "Application",
    "Appointment",
    "Completion",
  ],
  active = 1,
}: {
  steps?: string[];
  active?: number;
}) {
  return (
    <div className="stepper">
      {steps.map((step, i) => (
        <div className={`step ${i <= active ? "step-active" : ""}`} key={step}>
          <span>{i < active ? <Check size={14} /> : i + 1}</span>
          <small>{step}</small>
          {i < steps.length - 1 && <i />}
        </div>
      ))}
    </div>
  );
}
function Home() {
  return (
    <>
      <Header />
      <main className="home-page">
        <section className="hero">
          <div className="container hero-grid">
            <div className="hero-copy">
              <small className="eyebrow">OFFICIAL CIVIC GUIDE</small>
              <h1>
                Government services,
                <br />
                <em>made simple.</em>
              </h1>
              <p>
                Navigate passports, driving licenses, CNIC/NADRA paperwork, and
                government appointments in clear English or Urdu. Accurate.
                Safe. Built for all Pakistani citizens.
              </p>
              <HeroSearch />
              <div className="hero-trust">
                <ShieldCheck size={16} /> Independent guidance · Always verify
                on official portals
              </div>
            </div>
            <ResponsePreview />
          </div>
        </section>
        <Stats />
        <section className="section">
          <div className="container">
            <SectionHeader
              overline="BROWSE CATEGORIES"
              title="Popular Government Directories"
            />
            <div className="category-grid">
              {categoryData.map((item) => (
                <CategoryCard key={item[0]} item={item} />
              ))}
            </div>
          </div>
        </section>
        <section className="section cream">
          <div className="container">
            <SectionHeader
              overline="OUR PROCESS"
              title="Demystifying bureaucracy in seconds"
            />
            <div className="process-grid">
              {[
                [
                  "01",
                  "Ask in plain language",
                  "No complex bureaucratic terms. State your issue or question in English or Urdu just like you would to a helpful neighbor.",
                ],
                [
                  "02",
                  "Receive structured advice",
                  "Get a clear step-by-step roadmap outlining the mandatory documents, verified fees, links to official portals, and locators.",
                ],
                [
                  "03",
                  "Take guided action",
                  "Fill online forms, book pre-appointments, and track your applications directly with verified step guidance.",
                ],
              ].map(([num, title, text]) => (
                <div className="process-card" key={num}>
                  <span>{num}</span>
                  <h3>{title}</h3>
                  <p>{text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
        <section className="section journey">
          <div className="container">
            <SectionHeader
              overline="VISUAL WALKTHROUGH"
              title="Interactive Service Journeys"
              description="Watch how we trace every official requirement and turn a chaotic manual procedure into an orderly sequence."
            />
            <Stepper />
          </div>
        </section>
        <section className="section bilingual">
          <div className="container bilingual-grid">
            <div className="urdu-card" dir="rtl">
              <span>دھوپ میں زبان میں رہنمائی</span>
              <h3>شناختی کارڈ کی تجدید کیسے کریں؟</h3>
              <p>آپ کا سوال، ہماری رہنمائی۔</p>
              <div>
                ◆ اپنا اصل شناختی کارڈ
                <br />◆ حالیہ پاسپورٹ سائز تصویر
                <br />◆ ضروری دستاویزات اپنے پاس رکھیں
              </div>
            </div>
            <div>
              <SectionHeader
                overline="BILINGUAL ADVANTAGE"
                title="Local context engine. Real-time translation."
                description="No citizen should feel lost due to language barriers. PakAssist translates complex legal and bureaucratic terms instantly. Ask in English, read in Urdu, or vice-versa. Designed explicitly to serve diverse regions with absolute clarity."
              />
              <div className="button-row">
                <Button onClick={() => {}}>Try Urdu Version</Button>
                <Button variant="outline" onClick={() => {}}>
                  Read Accessibility Mandate
                </Button>
              </div>
            </div>
          </div>
        </section>
        <section className="section gateway" id="trust">
          <div className="container">
            <SectionHeader
              overline="OFFICIAL TRUST"
              title="Verified Official Gateways"
              description="We only reference directly sourced official federal and provincial portals. No third-party brokers."
            />
            <div className="gateway-grid">
              {[
                [
                  "NADRA Pakistan Portal",
                  "Direct access to register, modify and verify identity certificates.",
                  "nadra.gov.pk",
                ],
                [
                  "Directorate of Passports",
                  "Official link to machine-readable and e-passport application procedures.",
                  "dgip.gov.pk",
                ],
                [
                  "Federal Board of Revenue",
                  "The government body handling active taxpayers list and tax filing.",
                  "fbr.gov.pk",
                ],
              ].map((x) => (
                <a
                  className="gateway-card"
                  href={`https://${x[2]}`}
                  target="_blank"
                  rel="noreferrer"
                  key={x[0]}
                >
                  <b>{x[0]}</b>
                  <small>{x[1]}</small>
                  <span>{x[2]} ↗</span>
                </a>
              ))}
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
function ServiceCard({ service }: { service: Service }) {
  const icons: Record<string, typeof FileText> = {
    Passport: BookOpen,
    "CNIC/NADRA": CreditCard,
    "Driving License": CalendarDays,
    "Vehicle Registration": FileText,
    "Tax & Revenue": ShieldCheck,
    Documents: Landmark,
  };
  const Icon = icons[service.category] || FileText;
  return (
    <Link to={`/services/${service.slug}`} className="service-card">
      <div className="service-card-top">
        <span className="icon-tile">
          <Icon size={19} />
        </span>
        <span className="badge available">Available</span>
      </div>
      <small>{service.category}</small>
      <h3>{service.title}</h3>
      <p>{service.description}</p>
      <span className="card-link">
        View guide <ArrowRight size={15} />
      </span>
    </Link>
  );
}
function Services() {
  const [params] = useSearchParams();
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState(
    params.get("category") || "All Services",
  );
  const filtered = services.filter(
    (s) =>
      (category === "All Services" || s.category === category) &&
      `${s.title} ${s.description}`.toLowerCase().includes(query.toLowerCase()),
  );
  return (
    <>
      <Header />
      <main>
        <section className="page-band">
          <div className="container">
            <small className="eyebrow">YOUR NEXT STEP</small>
            <h1>Government Services</h1>
            <p>
              Find clear, practical guidance for the services that matter to
              you.
            </p>
          </div>
        </section>
        <section className="section services-page">
          <div className="container">
            <div className="directory-toolbar">
              <div className="directory-search">
                <Search size={18} />
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search services..."
                />
              </div>
              <span className="result-count">{filtered.length} services</span>
            </div>
            <div className="filter-pills">
              {["All Services", ...categories].map((x) => (
                <button
                  className={category === x ? "selected" : ""}
                  onClick={() => setCategory(x)}
                  key={x}
                >
                  {x}
                </button>
              ))}
            </div>
            {filtered.length ? (
              <div className="service-grid">
                {filtered.map((s) => (
                  <ServiceCard key={s.slug} service={s} />
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <Search size={28} />
                <h3>No services found</h3>
                <p>Try another search or clear the category filter.</p>
                <button
                  onClick={() => {
                    setQuery("");
                    setCategory("All Services");
                  }}
                >
                  Clear filters
                </button>
              </div>
            )}
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
function Detail() {
  const { slug } = useParams();
  const service = getService(slug || "");
  const [checked, setChecked] = useState<string[]>([]);
  if (!service)
    return (
      <>
        <Header />
        <div className="container not-found">
          <h1>Service not found</h1>
          <Link to="/services">Return to services</Link>
        </div>
      </>
    );
  return (
    <>
      <Header />
      <main>
        <section className="detail-head">
          <div className="container">
            <Link className="breadcrumb" to="/services">
              Services <ChevronRight size={14} /> {service.category}
            </Link>
            <div className="detail-title">
              <div>
                <span className="badge available">
                  <ShieldCheck size={14} /> Available
                </span>
                <h1>{service.title}</h1>
                <p>{service.authority}</p>
              </div>
              <Button
                onClick={() =>
                  alert(
                    "This mock action would open the official application gateway.",
                  )
                }
              >
                Start online application
              </Button>
            </div>
            <Stepper />
          </div>
        </section>
        <section className="section">
          <div className="container detail-layout">
            <div className="detail-content">
              <article className="content-block">
                <SectionHeader
                  overline="BEFORE YOU BEGIN"
                  title="Eligibility checklist"
                />
                {service.eligibility.map((x) => (
                  <div className="check-row" key={x}>
                    <span>
                      <Check size={15} />
                    </span>
                    {x}
                  </div>
                ))}
              </article>
              <article className="content-block">
                <SectionHeader
                  overline="PREPARE AHEAD"
                  title="Required documents"
                  description="Tap a document once you have it ready."
                />
                <div className="document-grid">
                  {service.documents.map((x) => (
                    <button
                      className={`document-card ${checked.includes(x) ? "checked" : ""}`}
                      key={x}
                      onClick={() =>
                        setChecked(
                          checked.includes(x)
                            ? checked.filter((y) => y !== x)
                            : [...checked, x],
                        )
                      }
                    >
                      <span>
                        {checked.includes(x) ? <Check /> : <FileText />}
                      </span>
                      <b>{x}</b>
                      <small>
                        {checked.includes(x) ? "Ready" : "Tap to mark ready"}
                      </small>
                    </button>
                  ))}
                </div>
              </article>
              <article className="content-block">
                <SectionHeader
                  overline="COSTS & TIMELINES"
                  title="Fee schedule"
                />
                <div className="fee-table">
                  <div className="fee-row fee-head">
                    <span>Delivery category</span>
                    <span>Processing fee</span>
                    <span>Timeline</span>
                  </div>
                  {service.fees.map((f) => (
                    <div className="fee-row" key={f.type}>
                      <b>{f.type}</b>
                      <span>{f.amount}</span>
                      <span>{f.timeline}</span>
                    </div>
                  ))}
                </div>
              </article>
              <article className="content-block">
                <SectionHeader
                  overline="YOUR ROADMAP"
                  title="Application process"
                />
                {service.processSteps.map((x, i) => (
                  <div className="guideline" key={x}>
                    <span>{String(i + 1).padStart(2, "0")}</span>
                    <div>
                      <b>{x}</b>
                      <p>
                        Keep your information accurate and ask the office to
                        clarify anything that differs in your case.
                      </p>
                    </div>
                  </div>
                ))}
              </article>
            </div>
            <aside className="detail-aside">
              <div className="ask-card">
                <span className="avatar large">P</span>
                <span className="badge verified-badge">
                  <ShieldCheck size={14} /> Verified
                </span>
                <h3>Have a question about this guide?</h3>
                <p>
                  Ask PakAssist for a simpler explanation or a personalized
                  checklist.
                </p>
                <Button onClick={() => (location.href = "/chat")}>
                  Ask PakAssist AI
                </Button>
              </div>
              <div className="related">
                <small>RELATED SERVICES</small>
                {service.relatedServices.map((title) => {
                  const r = services.find((x) => x.title === title);
                  return r ? (
                    <Link to={`/services/${r.slug}`} key={title}>
                      {title}
                      <ArrowRight size={15} />
                    </Link>
                  ) : null;
                })}
              </div>
            </aside>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
type ChatMsg = { from: "user" | "assistant"; text: string };
function AssistantResponse() {
  return (
    <div className="assistant-response">
      <p>For a passport renewal, you’ll generally need these items ready:</p>
      <div className="chat-checklist">
        {[
          "Original CNIC",
          "Previous passport",
          "Recent passport photograph",
          "Proof of address",
        ].map((x) => (
          <div key={x}>
            <Check size={14} />
            {x}
          </div>
        ))}
      </div>
      <div className="info-callout">
        <strong>Good to know</strong>
        <br />
        Fees and timelines depend on the processing category you choose. Verify
        the latest fee on dgip.gov.pk.
      </div>
      <small className="source">
        <ShieldCheck size={13} /> Source: Directorate General of Immigration &
        Passports — dgip.gov.pk
      </small>
    </div>
  );
}
function Chat() {
  const [params] = useSearchParams();
  const initial = params.get("query");
  const [messages, setMessages] = useState<ChatMsg[]>(
    initial
      ? [
          { from: "user", text: initial },
          {
            from: "assistant",
            text: "Here is a clear starting point for your question.",
          },
        ]
      : [
          {
            from: "user",
            text: "What documents do I need to renew my passport?",
          },
          {
            from: "assistant",
            text: "For a passport renewal, you’ll generally need these items ready:",
          },
        ],
  );
  const [input, setInput] = useState("");
  const [title, setTitle] = useState(initial || "Passport Renewal");
  const send = (text = input.trim()) => {
    if (!text) return;
    setMessages([
      ...messages,
      { from: "user", text },
      {
        from: "assistant",
        text: "Here is a practical guide based on the information available. I’ll keep the next steps clear and actionable.",
      },
    ]);
    setTitle(text);
    setInput("");
  };
  return (
    <>
      <Header />
      <main className="chat-page">
        <aside className="chat-sidebar">
          <Logo />
          <Button
            onClick={() => {
              setMessages([]);
              setTitle("New conversation");
            }}
          >
            New chat
          </Button>
          <div className="sidebar-search">
            <Search size={15} /> Search chats
          </div>
          <small>PINNED TOPICS</small>
          <Link to="/services/passport-renewal">
            <FileText size={15} /> Passport renewal
          </Link>
          <Link to="/services/cnic-renewal">
            <ClipboardCheck size={15} /> CNIC renewal
          </Link>
          <small>RECENT CHATS</small>
          <span className="chat-date">TODAY</span>
          <button className="chat-history active">Passport Renewal</button>
          <button className="chat-history">FBR tax filer guide</button>
          <span className="chat-date">YESTERDAY</span>
          <button className="chat-history">Learner permit requirements</button>
        </aside>
        <section className="chat-main">
          <div className="chat-toolbar">
            <div>
              <span className="online-dot" /> <b>{title}</b>
              <small>AI Agent Active</small>
            </div>
            <button className="language">
              <Globe2 size={14} /> EN / اردو
            </button>
          </div>
          <div className="message-thread">
            {messages.length === 0 ? (
              <div className="chat-empty">
                <Sparkles size={30} />
                <h2>What can we help you navigate?</h2>
                <p>Ask about a government service in plain language.</p>
              </div>
            ) : (
              messages.map((m, i) => (
                <div className={`message ${m.from}`} key={`${m.text}-${i}`}>
                  {m.from === "assistant" && <span className="avatar">P</span>}
                  <div className="bubble">
                    <p>{m.text}</p>
                    {m.from === "assistant" && <AssistantResponse />}
                  </div>
                </div>
              ))
            )}
            {messages.length > 0 && (
              <div className="followups">
                <span>Continue with</span>
                {[
                  "Normal or Urgent?",
                  "Adult or Minor?",
                  "Islamabad or Other City?",
                ].map((x) => (
                  <button key={x} onClick={() => send(x)}>
                    {x}
                    <ArrowRight size={13} />
                  </button>
                ))}
              </div>
            )}
          </div>
          <form
            className="chat-input"
            onSubmit={(e) => {
              e.preventDefault();
              send();
            }}
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a follow-up question..."
            />
            <span>Attachments coming soon</span>
            <button aria-label="Send message">
              <ArrowRight />
            </button>
          </form>
        </section>
      </main>
    </>
  );
}
function Dashboard() {
  const [notice, setNotice] = useState("");
  const action = (text: string) => {
    setNotice(`${text} is a mock action for now.`);
    setTimeout(() => setNotice(""), 2800);
  };
  return (
    <>
      <Header />
      <main>
        <section className="dashboard-head">
          <div className="container">
            <small className="eyebrow">YOUR PAKASSIST</small>
            <h1>Welcome back, Ahmed</h1>
            <p>Here’s a quick view of your civic service journey.</p>
          </div>
        </section>
        <section className="section dashboard-section">
          <div className="container">
            <div className="dash-stats">
              {[
                ["3", "Active Applications", "Across 2 services"],
                ["5 / 8", "Documents Prepared", "Passport Renewal"],
                ["1", "Upcoming Appointment", "Islamabad · 18 Jun"],
              ].map((x) => (
                <div className="dash-stat" key={x[1]}>
                  <span>{x[0]}</span>
                  <b>{x[1]}</b>
                  <small>{x[2]}</small>
                </div>
              ))}
            </div>
            <div className="dashboard-layout">
              <div>
                <div className="panel-heading">
                  <div>
                    <small>IN PROGRESS</small>
                    <h2>Your applications</h2>
                  </div>
                  <button onClick={() => action("Track application")}>
                    View all <ArrowRight size={15} />
                  </button>
                </div>
                <div className="applications">
                  {[
                    [
                      "Passport Renewal",
                      "PA-20481",
                      "Updated 2 hours ago",
                      "In Progress",
                    ],
                    [
                      "CNIC Renewal",
                      "PA-20392",
                      "Updated 3 days ago",
                      "Under Review",
                    ],
                    [
                      "Domicile Certificate",
                      "PA-19833",
                      "Completed 12 May",
                      "Completed",
                    ],
                  ].map((x) => (
                    <div className="application-row" key={x[1]}>
                      <span className="app-icon">
                        <FileText size={18} />
                      </span>
                      <div>
                        <b>{x[0]}</b>
                        <small>
                          {x[1]} · {x[2]}
                        </small>
                      </div>
                      <span
                        className={`badge ${x[3].toLowerCase().replace(" ", "-")}`}
                      >
                        {x[3]}
                      </span>
                      <ChevronRight size={17} />
                    </div>
                  ))}
                </div>
                <div className="panel-heading checklist-heading">
                  <div>
                    <small>DOCUMENT CHECKLIST</small>
                    <h2>Passport Renewal</h2>
                  </div>
                  <span>5 of 8 ready</span>
                </div>
                <div className="progress">
                  <span style={{ width: "62.5%" }} />
                </div>
              </div>
              <aside className="dash-side">
                <div className="appointment">
                  <small>NEXT APPOINTMENT</small>
                  <h3>Passport Office</h3>
                  <p>Blue Area, Islamabad</p>
                  <b>18 June 2025 · 10:30 AM</b>
                  <div>
                    <button onClick={() => action("Reschedule")}>
                      Reschedule
                    </button>
                    <button onClick={() => action("Cancel")}>Cancel</button>
                  </div>
                </div>
                <div className="quick">
                  <small>QUICK ACTIONS</small>
                  {[
                    ["Ask PakAssist AI", "Open chat"],
                    ["Track application", "Register"],
                    ["Book appointment", "Schedule"],
                    ["Saved documents", "Access"],
                  ].map((x) => (
                    <button onClick={() => action(x[0])} key={x[0]}>
                      <span>{x[1]}</span>
                      <b>{x[0]}</b>
                      <ArrowRight size={15} />
                    </button>
                  ))}
                </div>
              </aside>
            </div>
          </div>
        </section>
      </main>
      {notice && (
        <div className="toast">
          <Check size={16} />
          {notice}
        </div>
      )}
      <Footer />
    </>
  );
}
function InfoPage({ kind }: { kind: "how" | "about" }) {
  const [faq, setFaq] = useState(0);
  const faqs = [
    "Is PakAssist an official government entity?",
    "Is the service completely free to use?",
    "What departments and services are currently covered?",
    "How accurate is the information provided by the AI?",
    "Can I ask questions and receive guides in Urdu?",
  ];
  if (kind === "about")
    return (
      <>
        <Header />
        <main>
          <section className="page-band">
            <div className="container">
              <small className="eyebrow">OUR IDENTITY</small>
              <h1>About PakAssist</h1>
              <p>
                Building calmer, clearer pathways through everyday civic life.
              </p>
            </div>
          </section>
          <section className="section">
            <div className="container mission-grid">
              <div>
                <small className="eyebrow">THE MISSION</small>
                <h2>Bridging the gap between citizens and civic duties.</h2>
                <p>
                  PakAssist is open-source civic technology designed to make
                  public service information easier to understand and act on, in
                  English and Urdu.
                </p>
              </div>
              <div className="impact">
                <small>OUR CIVIC IMPACT TARGETS</small>
                {[
                  "Protecting citizens from fraudulent brokers",
                  "Democratic access in English & Urdu",
                  "Reducing hours lost in administrative lookup",
                ].map((x, i) => (
                  <div key={x}>
                    <span>0{i + 1}</span>
                    {x}
                  </div>
                ))}
              </div>
            </div>
          </section>
          <section className="section cream">
            <div className="container">
              <SectionHeader
                overline="THE EVERYDAY REALITY"
                title="Civic tasks shouldn’t feel like detective work."
              />
              <div className="reality-grid">
                {[
                  [
                    "Scattered guidelines",
                    "Information lives across too many offices and websites.",
                  ],
                  [
                    "Unclear costs & challans",
                    "Fees, timelines and requirements can be hard to compare.",
                  ],
                  [
                    "Exploitative agents",
                    "Confusion creates space for avoidable middlemen.",
                  ],
                ].map((x) => (
                  <div className="plain-card" key={x[0]}>
                    <span className="icon-tile">
                      <Gauge size={18} />
                    </span>
                    <h3>{x[0]}</h3>
                    <p>{x[1]}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>
          <section className="section">
            <div className="container">
              <SectionHeader
                overline="WHAT GUIDES US"
                title="Useful first. Always honest."
              />
              <div className="principles">
                {[
                  [
                    "Accurate Information",
                    "We organize guidance and point you back to the official source.",
                  ],
                  [
                    "Plain Language",
                    "We remove jargon without removing the details that matter.",
                  ],
                  [
                    "Step-by-Step Guidance",
                    "A clear next step is more useful than a wall of information.",
                  ],
                ].map((x) => (
                  <div key={x[0]}>
                    <span>✦</span>
                    <h3>{x[0]}</h3>
                    <p>{x[1]}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>
          <section className="section cream">
            <div className="container">
              <SectionHeader
                overline="CIVIC ROADMAP"
                title="Growing with the people we serve."
              />
              <div className="roadmap">
                {[
                  "PHASE 1 — Advanced Urdu Engine",
                  "PHASE 2 — WhatsApp Voice Assistant",
                  "PHASE 3 — Interactive Booking Integration",
                ].map((x, i) => (
                  <div key={x}>
                    <span>0{i + 1}</span>
                    <b>{x}</b>
                    <small>{i === 0 ? "In progress" : "Planned next"}</small>
                  </div>
                ))}
              </div>
            </div>
          </section>
          <section className="closing">
            <div>
              <small>OPEN-SOURCE CIVIC TECHNOLOGY</small>
              <h2>
                Built by Citizens,
                <br />
                For Citizens.
              </h2>
            </div>
            <Link to="/services" className="btn btn-outline">
              Explore services <ArrowRight size={16} />
            </Link>
          </section>
        </main>
        <Footer />
      </>
    );
  return (
    <>
      <Header />
      <main>
        <section className="page-band">
          <div className="container">
            <small className="eyebrow">STEP-BY-STEP SYSTEM</small>
            <h1>How PakAssist Works</h1>
            <p>
              A simpler way to understand the service journey before you take
              action.
            </p>
          </div>
        </section>
        <section className="section">
          <div className="container">
            <div className="how-cards">
              {[
                ["01", "INPUT", "Ask your question"],
                ["02", "ANALYSIS", "Get expert guidance"],
                ["03", "ACTION", "Take confident action"],
              ].map((x) => (
                <div className="how-card" key={x[0]}>
                  <span>{x[0]}</span>
                  <small>{x[1]}</small>
                  <h2>{x[2]}</h2>
                  <div className="snippet">
                    <Search size={15} /> Passport documents{" "}
                    <ArrowRight size={14} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
        <section className="section cream">
          <div className="container">
            <SectionHeader
              overline="CORE FUNCTIONS"
              title="Everything you need to move forward"
            />
            <div className="function-grid">
              {[
                "Document Requirements",
                "Fee Information",
                "Office Locations",
                "Appointment Booking",
                "Application Tracking",
                "Process Timelines",
              ].map((x) => (
                <div key={x}>
                  <Check size={17} />
                  <b>{x}</b>
                  <ArrowRight size={15} />
                </div>
              ))}
            </div>
          </div>
        </section>
        <section className="section">
          <div className="container transparency">
            <ShieldCheck size={24} />
            <div>
              <small>TRANSPARENCY NOTICE</small>
              <h2>
                Independent guidance, with official sources at the center.
              </h2>
              <p>
                PakAssist is independent and is not a government portal. We
                cannot process payments or submit applications. Always verify
                final information on official .gov.pk portals.
              </p>
            </div>
          </div>
        </section>
        <section className="section faq-section cream">
          <div className="container">
            <SectionHeader overline="COMMON QUESTIONS" title="Good to know" />
            <div className="faqs">
              {faqs.map((x, i) => (
                <div className={`faq ${faq === i ? "open" : ""}`} key={x}>
                  <button onClick={() => setFaq(faq === i ? -1 : i)}>
                    <b>{x}</b>
                    <ChevronDown size={18} />
                  </button>
                  {faq === i && (
                    <p>
                      {i === 0
                        ? "No. PakAssist is an independent civic-tech advisory and navigation platform."
                        : i === 1
                          ? "The guidance is free to use. Official fees, where applicable, are always listed separately."
                          : i === 2
                            ? "We currently cover passports, identity, driving, vehicle, tax, domicile and character certificate services."
                            : i === 3
                              ? "We structure mock guidance for this frontend and point you to official sources for verification."
                              : "Yes. You can ask questions in English or اردو."}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/services" element={<Services />} />
      <Route path="/services/:slug" element={<Detail />} />
      <Route path="/chat" element={<Chat />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/how-it-works" element={<InfoPage kind="how" />} />
      <Route path="/about" element={<InfoPage kind="about" />} />
      <Route path="*" element={<Home />} />
    </Routes>
  );
}
