import { useState } from "react";
import { Bar, BarChart, CartesianGrid, ReferenceLine, Tooltip, XAxis, YAxis } from "recharts";
import { CHART_COLOURS } from "../utils/chartTheme";
import { formatPounds } from "../utils/measures";
import ChartBox from "./ChartBox";
import ChartPanel from "./ChartPanel";
import MeasureKey from "./MeasureKey";

const KEYS = { gbp: "avg_change_gbp", pct: "pct_change" };

// Withheld cells (too few survey households) stay null: no bar, never £0.
export function decileRows(measures, unit = "gbp") {
  const key = KEYS[unit];
  return Array.from({ length: 10 }, (_, i) => {
    const row = { decile: i + 1 };
    for (const m of measures) row[m.id] = m.decile?.[i]?.[key] ?? null;
    return row;
  });
}

export function withheldDeciles(measures) {
  const out = new Set();
  for (const m of measures) for (const row of m.decile ?? []) if (row.suppressed) out.add(row.decile);
  return [...out].sort((a, b) => a - b);
}

export default function DistributionalChart({ measures, onMethod }) {
  const [unit, setUnit] = useState("gbp");
  const rows = decileRows(measures, unit);
  const withheld = withheldDeciles(measures);
  const format = unit === "gbp" ? formatPounds : (v) => (v === null ? "Withheld" : `${v.toFixed(2)}%`);
  return (
    <ChartPanel
      title="Change in household income by income decile"
      subtitle={unit === "gbp" ? "£ a year, average per household" : "% of household net income"}
      onMethod={onMethod}
      rows={rows}
      filename="deciles"
    >
      <div className="pill-row" role="group" aria-label="Unit">
        {[
          ["gbp", "£ a year"],
          ["pct", "% of income"],
        ].map(([value, label]) => (
          <button key={value} type="button" className={`pill ${unit === value ? "active" : ""}`} aria-pressed={unit === value} onClick={() => setUnit(value)}>
            {label}
          </button>
        ))}
      </div>
      <ChartBox>
        <BarChart data={rows}>
          <CartesianGrid stroke={CHART_COLOURS.grid} vertical={false} />
          <XAxis dataKey="decile" stroke={CHART_COLOURS.tick} interval={0} />
          <YAxis tickFormatter={unit === "gbp" ? formatPounds : (v) => `${v}%`} stroke={CHART_COLOURS.tick} width={60} />
          <Tooltip formatter={(v) => format(v)} />
          <ReferenceLine y={0} stroke={CHART_COLOURS.zeroLine} />
          {measures.map((m) => (
            <Bar isAnimationActive={false} key={m.id} dataKey={m.id} name={m.name} stackId="d" fill={m.colour} />
          ))}
        </BarChart>
      </ChartBox>
      <MeasureKey measures={measures} />
      {withheld.length > 0 && (
        <p className="m-0 mt-2 text-sm text-slate-600" data-testid="withheld-note">
          Withheld: too few survey households in decile {withheld.join(", ")}.
        </p>
      )}
    </ChartPanel>
  );
}
