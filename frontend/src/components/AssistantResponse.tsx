import { Check, ShieldCheck } from "lucide-react";

export default function AssistantResponse() {
  return (
    <div className="assistant-response">
      <p>For a passport renewal, you’ll generally need these items ready:</p>
      <div className="chat-checklist">
        {[
          "Original CNIC",
          "Previous passport",
          "Recent passport photograph",
          "Proof of address",
        ].map((x) => (
          <div key={x}>
            <Check size={14} />
            {x}
          </div>
        ))}
      </div>
      <div className="info-callout">
        <strong>Good to know</strong>
        <br />
        Fees and timelines depend on the processing category you choose. Verify
        the latest fee on dgip.gov.pk.
      </div>
      <small className="source">
        <ShieldCheck size={13} /> Source: Directorate General of Immigration &
        Passports — dgip.gov.pk
      </small>
    </div>
  );
}
