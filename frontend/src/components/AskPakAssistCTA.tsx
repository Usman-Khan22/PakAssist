import { ShieldCheck } from "lucide-react";
import Button from "./Button";

export default function AskPakAssistCTA() {
  return (
<div className="ask-card">
                <span className="avatar large">P</span>
                <span className="badge verified-badge">
                  <ShieldCheck size={14} /> Verified
                </span>
                <h3>Have a question about this guide?</h3>
                <p>
                  Ask PakAssist for a simpler explanation or a personalized
                  checklist.
                </p>
                <Button onClick={() => (location.href = "/chat")}>
                  Ask PakAssist AI
                </Button>
              </div>
  );
}
