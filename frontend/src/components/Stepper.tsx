import { copy, type LocalizedText } from "../translations";
import { useLanguage } from "../language";
import { Check } from "lucide-react";

export default function Stepper({
  steps = [
    copy.eligibility,
    copy.documents,
    copy.application,
    copy.appointment,
    copy.completion,
  ],
  active = 1,
}: {
  steps?: LocalizedText[];
  active?: number;
}) {
  const { localize } = useLanguage();
  return (
    <div className="stepper">
      {steps.map((step, i) => (
        <div className={`step ${i <= active ? "step-active" : ""}`} key={step.en}>
          <span>{i < active ? <Check size={14} /> : i + 1}</span>
          <small>{localize(step)}</small>
          {i < steps.length - 1 && <i />}
        </div>
      ))}
    </div>
  );
}
