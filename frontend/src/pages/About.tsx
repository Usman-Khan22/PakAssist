import { copy } from "../translations";
import { useLanguage } from "../language";
import { Link } from "react-router-dom";
import { ArrowRight, Gauge } from "lucide-react";
import Header from "../components/Header";
import Footer from "../components/Footer";
import SectionHeader from "../components/SectionHeader";

export default function About() {
  const { t, localize } = useLanguage();
    return (
      <>
        <Header />
        <main>
          <section className="page-band">
            <div className="container">
              <small className="eyebrow"> {t.ourIdentity} </small>
              <h1> {t.aboutPakassist} </h1>
              <p> {t.buildingCalmerClearerPathwaysThroughEverydayCivicLife} </p>
            </div>
          </section>
          <section className="section">
            <div className="container mission-grid">
              <div>
                <small className="eyebrow"> {t.theMission} </small>
                <h2> {t.bridgingTheGapBetweenCitizensAndCivicDuties} </h2>
                <p> {t.pakassistIsOpensourceCivicTechnologyDesignedToMakePublic} </p>
              </div>
              <div className="impact">
                <small> {t.ourCivicImpactTargets} </small>
                {[
                  copy.protectingCitizensFromFraudulentBrokers,
                  copy.democraticAccessInEnglishUrdu,
                  copy.reducingHoursLostInAdministrativeLookup,
                ].map((x, i) => (
                  <div key={localize(x)}>
                    <span>0{i + 1}</span>
                    {localize(x)}
                  </div>
                ))}
              </div>
            </div>
          </section>
          <section className="section cream">
            <div className="container">
              <SectionHeader
                overline={t.theEverydayReality}
                title={t.civicTasksShouldntFeelLikeDetectiveWork}
              />
              <div className="reality-grid">
                {[
                  [
                    copy.scatteredGuidelines,
                    copy.informationLivesAcrossTooManyOfficesAndWebsites,
                  ],
                  [
                    copy.unclearCostsChallans,
                    copy.feesTimelinesAndRequirementsCanBeHardToCompare,
                  ],
                  [
                    copy.exploitativeAgents,
                    copy.confusionCreatesSpaceForAvoidableMiddlemen,
                  ],
                ].map((x) => (
                  <div className="plain-card" key={localize(x[0])}>
                    <span className="icon-tile">
                      <Gauge size={18} />
                    </span>
                    <h3>{localize(x[0])}</h3>
                    <p>{localize(x[1])}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>
          <section className="section">
            <div className="container">
              <SectionHeader
                overline={t.whatGuidesUs}
                title={t.usefulFirstAlwaysHonest}
              />
              <div className="principles">
                {[
                  [
                    copy.accurateInformation,
                    copy.weOrganizeGuidanceAndPointYouBackToThe,
                  ],
                  [
                    copy.plainLanguage,
                    copy.weRemoveJargonWithoutRemovingTheDetailsThatMatter,
                  ],
                  [
                    copy.stepbystepGuidance,
                    copy.aClearNextStepIsMoreUsefulThanA,
                  ],
                ].map((x) => (
                  <div key={localize(x[0])}>
                    <span>✦</span>
                    <h3>{localize(x[0])}</h3>
                    <p>{localize(x[1])}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>
          <section className="section cream">
            <div className="container">
              <SectionHeader
                overline={t.civicRoadmap}
                title={t.growingWithThePeopleWeServe}
              />
              <div className="roadmap">
                {[
                  copy.phase1AdvancedUrduEngine,
                  copy.phase2WhatsappVoiceAssistant,
                  copy.phase3InteractiveBookingIntegration,
                ].map((x, i) => (
                  <div key={localize(x)}>
                    <span>0{i + 1}</span>
                    <b>{localize(x)}</b>
                    <small>{localize(i === 0 ? copy.inProgress3 : copy.plannedNext)}</small>
                  </div>
                ))}
              </div>
            </div>
          </section>
          <section className="closing">
            <div>
              <small> {t.opensourceCivicTechnology} </small>
              <h2> {t.builtByCitizens} <br /> {t.forCitizens} </h2>
            </div>
            <Link to="/services" className="secondary-button"> {t.exploreServices} <ArrowRight size={16} />
            </Link>
          </section>
        </main>
        <Footer />
      </>
    );
}
