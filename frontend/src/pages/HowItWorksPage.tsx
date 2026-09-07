import { copy } from "../translations";
import { useLanguage } from "../language";
import { useState } from "react";
import { ArrowRight, Check, ChevronDown, Search, ShieldCheck } from "lucide-react";
import Header from "../components/Header";
import Footer from "../components/Footer";
import SectionHeader from "../components/SectionHeader";

export default function HowItWorksPage() {
  const { t, localize } = useLanguage();
  const [faq, setFaq] = useState(0);
  const faqs = [
    copy.isPakassistAnOfficialGovernmentEntity,
    copy.isTheServiceCompletelyFreeToUse,
    copy.whatDepartmentsAndServicesAreCurrentlyCovered,
    copy.howAccurateIsTheInformationProvidedByTheAi,
    copy.canIAskQuestionsAndReceiveGuidesInUrdu,
  ];

  return (
    <>
      <Header />
      <main>
        <section className="page-band">
          <div className="container">
            <small className="eyebrow"> {t.stepbystepSystem} </small>
            <h1> {t.howPakassistWorks} </h1>
            <p> {t.aSimplerWayToUnderstandTheServiceJourneyBefore} </p>
          </div>
        </section>
        <section className="section">
          <div className="container">
            <div className="how-cards">
              {[
                ["01", copy.input, copy.askYourQuestion],
                ["02", copy.analysis, copy.getExpertGuidance],
                ["03", copy.action, copy.takeConfidentAction],
              ].map((x) => (
                <div className="how-card" key={localize(x[0])}>
                  <span>{localize(x[0])}</span>
                  <small>{localize(x[1])}</small>
                  <h2>{localize(x[2])}</h2>
                  <div className="snippet">
                    <Search size={15} /> {t.passportDocuments} {" "}
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
              overline={t.coreFunctions}
              title={t.everythingYouNeedToMoveForward}
            />
            <div className="function-grid">
              {[
                copy.documentRequirements,
                copy.feeInformation,
                copy.officeLocations,
                copy.appointmentBooking,
                copy.applicationTracking,
                copy.processTimelines,
              ].map((x) => (
                <div key={localize(x)}>
                  <Check size={17} />
                  <b>{localize(x)}</b>
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
              <small> {t.transparencyNotice} </small>
              <h2> {t.independentGuidanceWithOfficialSourcesAtTheCenter} </h2>
              <p> {t.pakassistIsIndependentAndIsNotAGovernmentPortal} </p>
            </div>
          </div>
        </section>
        <section className="section faq-section cream">
          <div className="container">
            <SectionHeader overline={t.commonQuestions} title={t.goodToKnow} />
            <div className="faqs">
              {faqs.map((x, i) => (
                <div className={`faq ${faq === i ? "open" : ""}`} key={localize(x)}>
                  <button onClick={() => setFaq(faq === i ? -1 : i)}>
                    <b>{localize(x)}</b>
                    <ChevronDown size={18} />
                  </button>
                  {faq === i && (
                    <p>
                      {localize(i === 0
                        ? copy.noPakassistIsAnIndependentCivictechAdvisoryAndNavigation
                        : i === 1
                          ? copy.theGuidanceIsFreeToUseOfficialFeesWhere
                          : i === 2
                            ? copy.weCurrentlyCoverPassportsIdentityDrivingVehicleTaxDomicile
                            : i === 3
                              ? copy.weStructureMockGuidanceForThisFrontendAndPoint
                              : copy.yesYouCanAskQuestionsInEnglishOr)}
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
