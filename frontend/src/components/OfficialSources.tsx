import { copy } from "../translations";
import { useLanguage } from "../language";
import SectionHeader from "./SectionHeader";

export default function OfficialSources() {
  const { t, localize } = useLanguage();
  return (
<section className="section gateway" id="sources">
          <div className="container">
            <SectionHeader
              overline={t.officialTrust}
              title={t.officialGovernmentSources}
              description={t.weOnlyReferenceDirectlySourcedOfficialFederalAndProvincial}
            />
            <div className="gateway-grid">
              {([
                [
                  copy.nadraPakistanPortal,
                  copy.directAccessToRegisterModifyAndVerifyIdentityCertificates,
                  "nadra.gov.pk",
                ],
                [
                  copy.directorateOfPassports,
                  copy.officialLinkToMachinereadableAndEpassportApplicationProcedures,
                  "dgip.gov.pk",
                ],
                [
                  copy.federalBoardOfRevenue,
                  copy.theGovernmentBodyHandlingActiveTaxpayersListAndTax,
                  "fbr.gov.pk",
                ],
              ] as const).map((x) => (
                <a
                  className="gateway-card"
                  href={`https://${x[2]}`}
                  target="_blank"
                  rel="noreferrer"
                  key={localize(x[0])}
                >
                  <b>{localize(x[0])}</b>
                  <small>{localize(x[1])}</small>
                  <span className="ltr-isolate" lang="en">{x[2]} ↗</span>
                </a>
              ))}
            </div>
          </div>
        </section>
  );
}
