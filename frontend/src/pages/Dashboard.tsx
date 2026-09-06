import { useState } from "react";
import { ArrowRight, Check, ChevronRight, FileText } from "lucide-react";
import Header from "../components/Header";
import Footer from "../components/Footer";

export default function Dashboard() {
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
