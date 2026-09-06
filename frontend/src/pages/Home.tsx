import { ShieldCheck } from "lucide-react";
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
  return (
    <>
      <Header />
      <main className="home-page">
        <section className="hero">
          <div className="container hero-grid">
            <div className="hero-copy">
              <small className="eyebrow">OFFICIAL CIVIC GUIDE</small>
              <h1>
                Government services,
                <br />
                <em>made simple.</em>
              </h1>
              <p>
                Navigate passports, driving licenses, CNIC/NADRA paperwork, and
                government appointments in clear English or Urdu. Accurate.
                Safe. Built for all Pakistani citizens.
              </p>
              <HeroSearch />
              <div className="hero-trust">
                <ShieldCheck size={16} /> Independent guidance · Always verify
                on official portals
              </div>
            </div>
            <ResponsePreview />
          </div>
        </section>
        <TrustRow />
        <section className="section">
          <div className="container">
            <SectionHeader
              overline="BROWSE CATEGORIES"
              title="Popular Government Directories"
            />
            <ServiceGrid />
          </div>
        </section>
        <HowItWorks />
        <section className="section journey">
          <div className="container">
            <SectionHeader
              overline="VISUAL WALKTHROUGH"
              title="Interactive Service Journeys"
              description="Watch how we trace every official requirement and turn a chaotic manual procedure into an orderly sequence."
            />
            <Stepper />
          </div>
        </section>
        <section className="section bilingual">
          <div className="container bilingual-grid">
            <div className="urdu-card" lang="ur" dir="rtl">
              <span>دھوپ میں زبان میں رہنمائی</span>
              <h3 className="urdu-heading">شناختی کارڈ کی تجدید کیسے کریں؟</h3>
              <p>آپ کا سوال، ہماری رہنمائی۔</p>
              <div>
                ◆ اپنا اصل شناختی کارڈ
                <br />◆ حالیہ پاسپورٹ سائز تصویر
                <br />◆ ضروری دستاویزات اپنے پاس رکھیں
              </div>
            </div>
            <div>
              <SectionHeader
                overline="BILINGUAL ADVANTAGE"
                title="Local context engine. Real-time translation."
                description="No citizen should feel lost due to language barriers. PakAssist translates complex legal and bureaucratic terms instantly. Ask in English, read in Urdu, or vice-versa. Designed explicitly to serve diverse regions with absolute clarity."
              />
              <div className="button-row">
                <Button onClick={() => {}}>Try Urdu Version</Button>
                <Button variant="secondary" onClick={() => {}}>
                  Read Accessibility Mandate
                </Button>
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
