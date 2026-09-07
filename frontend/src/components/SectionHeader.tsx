import { useLanguage } from "../language";
export default function SectionHeader({
  overline,
  title,
  description,
}: {
  overline: string;
  title: string;
  description?: string;
}) {
  const { localize } = useLanguage();
  return (
    <div className="section-head">
      <small>{localize(overline)}</small>
      <h2>{localize(title)}</h2>
      <div className="diamonds">
        <i />
        <i />
        <i />
      </div>
      {description && <p>{localize(description)}</p>}
    </div>
  );
}
