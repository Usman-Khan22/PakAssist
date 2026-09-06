import { Link } from "react-router-dom";
import { ArrowRight, Gauge } from "lucide-react";
import Header from "../components/Header";
import Footer from "../components/Footer";
import SectionHeader from "../components/SectionHeader";

export default function About() {
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
            <Link to="/services" className="secondary-button">
              Explore services <ArrowRight size={16} />
            </Link>
          </section>
        </main>
        <Footer />
      </>
    );
}
