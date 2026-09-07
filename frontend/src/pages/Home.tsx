import { useLanguage } from "../language";
import { ShieldCheck } from "lucide-react";
import { useUrdu, setStoredLanguage } from "../language";
import Button from "../components/Button";
import Header from "../components/Header";
import Footer from "../components/Footer";
import SectionHeader from "../components/SectionHeader";
import HeroSearch from "../components/HeroSearch";
import ResponsePreview from "../components/ResponsePreview";
import Stepper from "../components/Stepper";
import TrustRow from "../components/TrustRow";
import HowItWorks from "../components/HowItWorks";
import OfficialSources from "../components/OfficialSources";
import ServiceGrid from "../components/ServiceGrid";

export default function Home() {
  const { t, language } = useLanguage();
  const urdu = useUrdu();
  return (
    <>
      <Header />
      <main className="home-page">
        <section className="hero">
          <div className="container hero-grid">
            <div className="hero-copy">
              <small className="eyebrow"> {t.officialCivicGuide} </small>
              <h1 className={urdu ? "urdu-heading" : ""}>
                <> {t.governmentServices} <br />
                <em> {t.madeSimple} </em>
                </>
              </h1>
              <p>
                <> {t.navigatePassportsDrivingLicensesCnicnadraPaperworkAndGovernmentAppointments} </>
              </p>
              <HeroSearch />
              <div className="hero-trust">
                <ShieldCheck size={16} /> {t.independentGuidanceAlwaysVerifyOnOfficialPortals} </div>
            </div>
            <ResponsePreview />
          </div>
        </section>
        <TrustRow />
        <section className="section">
          <div className="container">
            <SectionHeader
              overline={t.browseCategories}
              title={t.popularGovernmentDirectories}
            />
            <ServiceGrid />
          </div>
        </section>
        <HowItWorks />
        <section className="section journey">
          <div className="container">
            <SectionHeader
              overline={t.visualWalkthrough}
              title={t.interactiveServiceJourneys}
              description={t.watchHowWeTraceEveryOfficialRequirementAndTurn}
            />
            <Stepper />
          </div>
        </section>
        <section className="section bilingual">
          <div className="container bilingual-grid">
            <div className="urdu-card" lang={language} dir={urdu ? "rtl" : "ltr"}>
              <span> {t.guidanceInYourLanguage} </span>
              <h3 className={urdu ? "urdu-heading" : ""}> {t.howDoIRenewMyCnic} </h3>
              <p> {t.yourQuestionOurGuidance} </p>
              <div> {t.yourOriginalCnic} <br /> {t.aRecentPassportPhotograph} <br /> {t.keepRequiredDocumentsReady} </div>
            </div>
            <div>
              <SectionHeader
                overline={t.bilingualAdvantage}
                title={t.localContextEngineRealtimeTranslation}
                description={t.noCitizenShouldFeelLostDueToLanguageBarriers}
              />
              <div className="button-row">
                <Button onClick={() => setStoredLanguage(true)}> {t.tryUrduVersion} </Button>
                <Button variant="secondary" onClick={() => {}}> {t.readAccessibilityMandate} </Button>
              </div>
            </div>
          </div>
        </section>
        <OfficialSources />
      </main>
      <Footer />
    </>
  );
}
