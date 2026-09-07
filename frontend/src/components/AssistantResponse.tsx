import { copy } from "../translations";
import { useLanguage } from "../language";
import { Check, ShieldCheck } from "lucide-react";

export default function AssistantResponse() {
  const { t, localize } = useLanguage();
  return (
    <div className="assistant-response">
      <p> {t.forAPassportRenewalYoullGenerallyNeedTheseItems} </p>
      <div className="chat-checklist">
        {[
          copy.originalCnic,
          copy.previousPassport,
          copy.recentPassportPhotograph,
          copy.proofOfAddress,
        ].map((x) => (
          <div key={localize(x)}>
            <Check size={14} />
            {localize(x)}
          </div>
        ))}
      </div>
      <div className="info-callout">
        <strong> {t.goodToKnow} </strong>
        <br /> {t.feesAndTimelinesDependOnTheProcessingCategoryYou} </div>
      <small className="source">
        <ShieldCheck size={13} /> {t.sourceDirectorateGeneralOfImmigrationPassportsDgipgovpk} </small>
    </div>
  );
}
