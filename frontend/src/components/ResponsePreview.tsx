import { Check, ShieldCheck } from "lucide-react";

export default function ResponsePreview() {
  return (
    <div className="response-preview">
      <div className="response-top">
        <span className="verified">
          <ShieldCheck size={15} /> Verified guidance
        </span>
        <span>Just now</span>
      </div>
      <p className="question">“What documents do I need to renew my CNIC?”</p>
      <div className="assistant-line">
        <span className="avatar">P</span>
        <p>
          You’ll need your original CNIC and a recent photograph. Here’s the
          complete checklist:
        </p>
      </div>
      <div className="mini-checks">
        {[
          "Original CNIC",
          "Recent photograph",
          "Proof of address",
          "Fee payment receipt",
        ].map((x) => (
          <div key={x}>
            <Check size={15} />
            {x}
          </div>
        ))}
      </div>
      <div className="info-strip">
        <span>i</span> Requirements can vary by case. Verify at nadra.gov.pk
      </div>
    </div>
  );
}
