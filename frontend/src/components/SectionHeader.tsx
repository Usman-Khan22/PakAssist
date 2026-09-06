export default function SectionHeader({
  overline,
  title,
  description,
}: {
  overline: string;
  title: string;
  description?: string;
}) {
  return (
    <div className="section-head">
      <small>{overline}</small>
      <h2>{title}</h2>
      <div className="diamonds">
        <i />
        <i />
        <i />
      </div>
      {description && <p>{description}</p>}
    </div>
  );
}
