import { Check } from "lucide-react";

export default function Stepper({
  steps = [
    "Eligibility",
    "Documents",
    "Application",
    "Appointment",
    "Completion",
  ],
  active = 1,
}: {
  steps?: string[];
  active?: number;
}) {
  return (
    <div className="stepper">
      {steps.map((step, i) => (
        <div className={`step ${i <= active ? "step-active" : ""}`} key={step}>
          <span>{i < active ? <Check size={14} /> : i + 1}</span>
          <small>{step}</small>
          {i < steps.length - 1 && <i />}
        </div>
      ))}
    </div>
  );
}
