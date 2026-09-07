import { useLanguage } from "../language";
export default function TrustRow() {
  const { t } = useLanguage();
  return (
    <div className="stats">
      <div>
        <b>
          50,000<span>+</span>
        </b>
        <small> {t.citizensGuided} </small>
      </div>
      <div>
        <b>
          200<span>+</span>
        </b>
        <small> {t.servicesCataloged} </small>
      </div>
      <div>
        <b>24/7</b>
        <small> {t.instantAvailability} </small>
      </div>
      <div>
        <b>{t.bilingualLanguages}</b>
        <small> {t.bilingualSupport} </small>
      </div>
    </div>
  );
}
