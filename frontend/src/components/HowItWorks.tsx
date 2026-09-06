import SectionHeader from "./SectionHeader";

export default function HowItWorks() {
  return (
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
  );
}
