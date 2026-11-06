// Chips for the computable measures; selection is kept in ?policies=.
// Selected chips change fill and border only.
export default function PolicySelector({ measures, selected, onChange }) {
  const toggle = (id) =>
    onChange(selected.includes(id) ? selected.filter((s) => s !== id) : [...selected, id]);
  return (
    <div className="mb-6 grid gap-3 sm:grid-cols-2" role="group" aria-label="Measures">
      {measures.map((m) => (
        <button
          key={m.id}
          type="button"
          aria-pressed={selected.includes(m.id)}
          className={`selector-chip ${selected.includes(m.id) ? "active" : ""}`}
          onClick={() => toggle(m.id)}
        >
          <span className="inline-block h-3 w-3 rounded-full align-middle" style={{ background: m.colour }} />
          <span className="ml-2 font-semibold text-slate-800">{m.name}</span>
          <span className="mt-1 block text-sm text-slate-500">{m.description}</span>
        </button>
      ))}
    </div>
  );
}
