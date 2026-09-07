import { useLanguage } from "../language";
import { ShieldCheck } from "lucide-react";
import Button from "./Button";

export default function AskPakAssistCTA() {
  const { t } = useLanguage();
  return (
<div className="ask-card">
                <span className="avatar large">P</span>
                <span className="badge verified-badge">
                  <ShieldCheck size={14} /> {t.verified} </span>
                <h3> {t.haveAQuestionAboutThisGuide} </h3>
                <p> {t.askPakassistForASimplerExplanationOrAPersonalized} </p>
                <Button onClick={() => (location.href = "/chat")}> {t.askPakassistAi} </Button>
              </div>
  );
}
