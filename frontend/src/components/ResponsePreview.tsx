import { copy } from "../translations";
import { useLanguage } from "../language";
import { Check, ShieldCheck } from "lucide-react";

export default function ResponsePreview() {
  const { t, localize } = useLanguage();
  return (
    <div className="response-preview">
      <div className="response-top">
        <span className="verified">
          <ShieldCheck size={15} /> {t.verifiedGuidance} </span>
        <span> {t.justNow} </span>
      </div>
      <p className="question"> {t.whatDocumentsDoINeedToRenewMyCnic} </p>
      <div className="assistant-line">
        <span className="avatar">P</span>
        <p> {t.youllNeedYourOriginalCnicAndARecentPhotograph} </p>
      </div>
      <div className="mini-checks">
        {[
          copy.originalCnic,
          copy.recentPhotograph,
          copy.proofOfAddress,
          copy.feePaymentReceipt,
        ].map((x) => (
          <div key={localize(x)}>
            <Check size={15} />
            {localize(x)}
          </div>
        ))}
      </div>
      <div className="info-strip">
        <span>i</span> {t.requirementsCanVaryByCaseVerifyAtNadragovpk} </div>
    </div>
  );
}
