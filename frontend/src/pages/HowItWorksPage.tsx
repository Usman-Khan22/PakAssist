import { useState } from "react";
import { ArrowRight, Check, ChevronDown, Search, ShieldCheck } from "lucide-react";
import Header from "../components/Header";
import Footer from "../components/Footer";
import SectionHeader from "../components/SectionHeader";

export default function HowItWorksPage() {
  const [faq, setFaq] = useState(0);
  const faqs = [
    "Is PakAssist an official government entity?",
    "Is the service completely free to use?",
    "What departments and services are currently covered?",
    "How accurate is the information provided by the AI?",
    "Can I ask questions and receive guides in Urdu?",
  ];

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
