// Legend for charts that stack the selected measures.
export default function MeasureKey({ measures }) {
  if (!measures.length) return null;
  return (
    <div className="measure-key" data-testid="measure-key">
      {measures.map((m) => (
        <span key={m.id}>
          <span className="swatch" style={{ background: m.colour }} />
          {m.name}
        </span>
      ))}
    </div>
  );
}
