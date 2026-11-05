export default function StatTiles({ tiles }) {
  return (
    <div className="mb-6 grid gap-4 sm:grid-cols-3">
      {tiles.map((tile) => (
        <div key={tile.label} className="metric-card">
          <p className="eyebrow m-0 text-slate-500">{tile.label}</p>
          <p className="m-0 mt-2 text-2xl font-bold text-slate-800">{tile.value}</p>
          {tile.note && <p className="m-0 mt-1 text-xs text-slate-500">{tile.note}</p>}
        </div>
      ))}
    </div>
  );
}
