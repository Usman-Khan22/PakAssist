import { copy, type LocalizedText } from "../translations";
import { useLanguage } from "../language";
import { useState } from "react";
import { ArrowRight, Check, ChevronRight, FileText } from "lucide-react";
import Header from "../components/Header";
import Footer from "../components/Footer";

export default function Dashboard() {
  const { t, language, localize } = useLanguage();
  const [notice, setNotice] = useState<LocalizedText | null>(null);
  const action = (text: LocalizedText) => {
    setNotice(text);
    setTimeout(() => setNotice(null), 2800);
  };
  return (
    <>
      <Header />
      <main>
        <section className="dashboard-head">
          <div className="container">
            <small className="eyebrow"> {t.yourPakassist} </small>
            <h1> {t.welcomeBackAhmed} </h1>
            <p> {t.heresAQuickViewOfYourCivicServiceJourney} </p>
          </div>
        </section>
        <section className="section dashboard-section">
          <div className="container">
            <div className="dash-stats">
              {([
                ["3", copy.activeApplications, copy.across2Services],
                ["5 / 8", copy.documentsPrepared, copy.passportRenewal],
                ["1", copy.upcomingAppointment, copy.islamabad18Jun],
              ] as const).map((x) => (
                <div className="dash-stat" key={localize(x[1])}>
                  <span>{localize(x[0])}</span>
                  <b>{localize(x[1])}</b>
                  <small>{localize(x[2])}</small>
                </div>
              ))}
            </div>
            <div className="dashboard-layout">
              <div>
                <div className="panel-heading">
                  <div>
                    <small> {t.inProgress} </small>
                    <h2> {t.yourApplications} </h2>
                  </div>
                  <button onClick={() => action(copy.trackApplication)}> {t.viewAll} <ArrowRight size={15} />
                  </button>
                </div>
                <div className="applications">
                  {[
                    [
                      copy.passportRenewal,
                      "PA-20481",
                      copy.updated2HoursAgo,
                      copy.inProgress2,
                    ],
                    [
                      copy.cnicRenewal,
                      "PA-20392",
                      copy.updated3DaysAgo,
                      copy.underReview,
                    ],
                    [
                      copy.domicileCertificate,
                      "PA-19833",
                      copy.completed12May,
                      copy.completed,
                    ],
                  ].map((x) => (
                    <div className="application-row" key={localize(x[1])}>
                      <span className="app-icon">
                        <FileText size={18} />
                      </span>
                      <div>
                        <b>{localize(x[0])}</b>
                        <small>
                          {localize(x[1])} · {localize(x[2])}
                        </small>
                      </div>
                      <span
                        className={`badge ${(typeof x[3] === "string" ? x[3] : x[3].en).toLowerCase().replace(" ", "-")}`}
                      >
                        {localize(x[3])}
                      </span>
                      <ChevronRight size={17} />
                    </div>
                  ))}
                </div>
                <div className="panel-heading checklist-heading">
                  <div>
                    <small> {t.documentChecklist} </small>
                    <h2> {t.passportRenewal} </h2>
                  </div>
                  <span> {t.value5Of8Ready} </span>
                </div>
                <div className="progress">
                  <span style={{ width: "62.5%" }} />
                </div>
              </div>
              <aside className="dash-side">
                <div className="appointment">
                  <small> {t.nextAppointment} </small>
                  <h3> {t.passportOffice} </h3>
                  <p> {t.blueAreaIslamabad} </p>
                  <b> {t.value18June20251030Am} </b>
                  <div>
                    <button onClick={() => action(copy.reschedule)}> {t.reschedule} </button>
                    <button onClick={() => action(copy.cancel)}> {t.cancel} </button>
                  </div>
                </div>
                <div className="quick">
                  <small> {t.quickActions} </small>
                  {[
                    [copy.askPakassistAi, copy.openChat],
                    [copy.trackApplication, copy.register],
                    [copy.bookAppointment, copy.schedule],
                    [copy.savedDocuments, copy.access],
                  ].map((x) => (
                    <button onClick={() => action(x[0])} key={localize(x[0])}>
                      <span>{localize(x[1])}</span>
                      <b>{localize(x[0])}</b>
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
          {localize(copy.actionIsAMockActionForNow[language].replace('{action}', notice[language]))}
        </div>
      )}
      <Footer />
    </>
  );
}
