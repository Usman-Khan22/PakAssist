import { categoryLabels } from "../data";
import { useLanguage } from "../language";
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
  const { t, language, localize } = useLanguage();
  const { slug } = useParams();
  const service = getService(slug || "");
  const [checked, setChecked] = useState<string[]>([]);
  if (!service)
    return (
      <>
        <Header />
        <div className="container not-found">
          <h1> {t.serviceNotFound} </h1>
          <Link to="/services"> {t.returnToServices} </Link>
        </div>
      </>
    );
  return (
    <>
      <Header />
      <main>
        <section className="detail-head">
          <div className="container">
            <Link className="breadcrumb" to="/services"> {t.services} <ChevronRight size={14} /> {localize(categoryLabels[service.category])}
            </Link>
            <div className="detail-title">
              <div>
                <span className="badge available">
                  <ShieldCheck size={14} /> {t.available} </span>
                <h1>{localize(service.title[language])}</h1>
                <p>{localize(service.authority[language])}</p>
              </div>
              <Button
                onClick={() =>
                  alert(
                    t.thisMockActionWouldOpenTheOfficialApplicationGateway,
                  )
                }
              > {t.startOnlineApplication} </Button>
            </div>
            <Stepper />
          </div>
        </section>
        <section className="section">
          <div className="container detail-layout">
            <div className="detail-content">
              <article className="content-block">
                <SectionHeader
                  overline={t.beforeYouBegin}
                  title={t.eligibilityChecklist}
                />
                {service.eligibility.map((x) => (
                  <div className="check-row" key={x.en}>
                    <span>
                      <Check size={15} />
                    </span>
                    {localize(x)}
                  </div>
                ))}
              </article>
              <article className="content-block">
                <SectionHeader
                  overline={t.prepareAhead}
                  title={t.requiredDocuments}
                  description={t.tapADocumentOnceYouHaveItReady}
                />
                <div className="document-grid">
                  {service.documents.map((x) => (
                    <button
                      className={`document-card ${checked.includes(`${service.slug}:${x.en}`) ? "checked" : ""}`}
                      key={x.en}
                      onClick={() =>
                        setChecked(
                          checked.includes(`${service.slug}:${x.en}`)
                            ? checked.filter((y) => y !== `${service.slug}:${x.en}`)
                            : [...checked, `${service.slug}:${x.en}`],
                        )
                      }
                    >
                      <span>
                        {checked.includes(`${service.slug}:${x.en}`) ? <Check /> : <FileText />}
                      </span>
                      <b>{localize(x)}</b>
                      <small>
                        {checked.includes(`${service.slug}:${x.en}`) ? t.ready : t.tapToMarkReady}
                      </small>
                    </button>
                  ))}
                </div>
              </article>
              <article className="content-block">
                <SectionHeader
                  overline={t.costsTimelines}
                  title={t.feeSchedule}
                />
                <div className="fee-table">
                  <div className="fee-row fee-head">
                    <span> {t.deliveryCategory} </span>
                    <span> {t.processingFee} </span>
                    <span> {t.timeline} </span>
                  </div>
                  {service.fees.map((f) => (
                    <div className="fee-row" key={f.type.en}>
                      <b>{localize(f.type[language])}</b>
                      <span>{localize(f.amount[language])}</span>
                      <span>{localize(f.timeline[language])}</span>
                    </div>
                  ))}
                </div>
              </article>
              <article className="content-block">
                <SectionHeader
                  overline={t.yourRoadmap}
                  title={t.applicationProcess}
                />
                {service.processSteps.map((x, i) => (
                  <div className="guideline" key={x.en}>
                    <span>{String(i + 1).padStart(2, "0")}</span>
                    <div>
                      <b>{localize(x)}</b>
                      <p> {t.keepYourInformationAccurateAndAskTheOfficeTo} </p>
                    </div>
                  </div>
                ))}
              </article>
            </div>
            <aside className="detail-aside">
              <AskPakAssistCTA />
              <div className="related">
                <small> {t.relatedServices} </small>
                {service.relatedServices.map((title) => {
                  const r = services.find((x) => x.title.en === title.en);
                  return r ? (
                    <Link to={`/services/${r.slug}`} key={r.slug}>
                      {localize(title)}
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
