import SectionHeader from "./SectionHeader";

export default function OfficialSources() {
  return (
<section className="section gateway" id="trust">
          <div className="container">
            <SectionHeader
              overline="OFFICIAL TRUST"
              title="Verified Official Gateways"
              description="We only reference directly sourced official federal and provincial portals. No third-party brokers."
            />
            <div className="gateway-grid">
              {[
                [
                  "NADRA Pakistan Portal",
                  "Direct access to register, modify and verify identity certificates.",
                  "nadra.gov.pk",
                ],
                [
                  "Directorate of Passports",
                  "Official link to machine-readable and e-passport application procedures.",
                  "dgip.gov.pk",
                ],
                [
                  "Federal Board of Revenue",
                  "The government body handling active taxpayers list and tax filing.",
                  "fbr.gov.pk",
                ],
              ].map((x) => (
                <a
                  className="gateway-card"
                  href={`https://${x[2]}`}
                  target="_blank"
                  rel="noreferrer"
                  key={x[0]}
                >
                  <b>{x[0]}</b>
                  <small>{x[1]}</small>
                  <span>{x[2]} ↗</span>
                </a>
              ))}
            </div>
          </div>
        </section>
  );
}
