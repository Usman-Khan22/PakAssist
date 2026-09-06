import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowRight, Check, ChevronRight, FileText, ShieldCheck } from "lucide-react";
import { getService, services } from "../data";
import Button from "../components/Button";
import Header from "../components/Header";
import Footer from "../components/Footer";
import SectionHeader from "../components/SectionHeader";
import Stepper from "../components/Stepper";
import AskPakAssistCTA from "../components/AskPakAssistCTA";

export default function ServiceDetail() {
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
              <AskPakAssistCTA />
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
