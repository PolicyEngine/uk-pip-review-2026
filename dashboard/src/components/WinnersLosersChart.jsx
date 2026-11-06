import { Bar, BarChart, CartesianGrid, Legend, Tooltip, XAxis, YAxis } from "recharts";
import { CHART_COLOURS, WINNERS_LOSERS_SERIES } from "../utils/chartTheme";
import ChartBox from "./ChartBox";
import ChartPanel from "./ChartPanel";
import EmptyState from "./EmptyState";

// One entry at a time: a single measure, or the package of all modelled
// measures when a model run has produced it. An "All" row sits above
// decile 1 when the entry has one.
export default function WinnersLosersChart({ options, active, onChange }) {
  const entry = options.find((o) => o.id === active) ?? options[0];
  const rows = entry?.winners_losers
    ? [...(entry.winners_losers_all ? [{ ...entry.winners_losers_all, decile: "All" }] : []), ...entry.winners_losers]
    : [];
  const withheld = rows.filter((r) => r.suppressed).map((r) => r.decile);
  return (
    <ChartPanel title="Who gains and who loses" subtitle="Share of people, by household income decile, %" rows={rows} filename="winners-losers">
      <div className="pill-row" role="group" aria-label="Measure">
        {options.map((o) => (
          <button key={o.id} type="button" className={`pill ${entry?.id === o.id ? "active" : ""}`} aria-pressed={entry?.id === o.id} onClick={() => onChange(o.id)}>
            {o.label}
          </button>
        ))}
      </div>
      {rows.length ? (
        <ChartBox height={400}>
          <BarChart data={rows} layout="vertical">
            <CartesianGrid stroke={CHART_COLOURS.grid} horizontal={false} />
            <XAxis type="number" domain={[0, 100]} stroke={CHART_COLOURS.tick} />
            <YAxis type="category" dataKey="decile" stroke={CHART_COLOURS.tick} width={36} interval={0} />
            <Tooltip formatter={(v) => (v === null ? "Withheld" : `${v}%`)} />
            <Legend />
            {WINNERS_LOSERS_SERIES.map((s) => (
              <Bar isAnimationActive={false} key={s.key} dataKey={s.key} name={s.label} stackId="wl" fill={s.colour} />
            ))}
          </BarChart>
        </ChartBox>
      ) : (
        <EmptyState>The package of all modelled measures is shown once a model run has produced it.</EmptyState>
      )}
      {withheld.length > 0 && (
        <p className="m-0 mt-2 text-sm text-slate-600">Withheld: too few survey households in decile {withheld.join(", ")}.</p>
      )}
    </ChartPanel>
  );
}
