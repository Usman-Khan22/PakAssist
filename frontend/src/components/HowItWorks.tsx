import { copy } from "../translations";
import { useLanguage } from "../language";
import SectionHeader from "./SectionHeader";

export default function HowItWorks() {
  const { t, localize } = useLanguage();
  return (
<section className="section cream">
          <div className="container">
            <SectionHeader
              overline={t.ourProcess}
              title={t.demystifyingBureaucracyInSeconds}
            />
            <div className="process-grid">
              {[
                [
                  "01",
                  copy.askInPlainLanguage,
                  copy.noComplexBureaucraticTermsStateYourIssueOrQuestion,
                ],
                [
                  "02",
                  copy.receiveStructuredAdvice,
                  copy.getAClearStepbystepRoadmapOutliningTheMandatoryDocuments,
                ],
                [
                  "03",
                  copy.takeGuidedAction,
                  copy.fillOnlineFormsBookPreappointmentsAndTrackYourApplications,
                ],
              ].map(([num, title, text]) => (
                <div className="process-card" key={localize(num)}>
                  <span>{localize(num)}</span>
                  <h3>{localize(title)}</h3>
                  <p>{localize(text)}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
  );
}
