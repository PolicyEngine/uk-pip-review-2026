import { Bar, BarChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CHART_COLOURS } from "../utils/chartTheme";
import { formatPounds } from "../utils/measures";
import ChartPanel from "./ChartPanel";

export function decileRows(measures) {
  return Array.from({ length: 10 }, (_, i) => {
    const row = { decile: i + 1 };
    for (const m of measures) row[m.id] = m.decile?.[i]?.avg_change_gbp ?? 0;
    return row;
  });
}

export default function DistributionalChart({ measures, basis }) {
  const rows = decileRows(measures);
  return (
    <ChartPanel title="Average change in household income by decile" subtitle={basis} rows={rows} filename="deciles">
      <div style={{ width: "100%", height: 320 }}>
        <ResponsiveContainer>
          <BarChart data={rows}>
            <CartesianGrid stroke={CHART_COLOURS.grid} vertical={false} />
            <XAxis dataKey="decile" stroke={CHART_COLOURS.tick} />
            <YAxis tickFormatter={formatPounds} stroke={CHART_COLOURS.tick} width={60} />
            <Tooltip formatter={(v) => formatPounds(v)} />
            <ReferenceLine y={0} stroke={CHART_COLOURS.zeroLine} />
            {measures.map((m) => (
              <Bar isAnimationActive={false} key={m.id} dataKey={m.id} name={m.name} stackId="d" fill={m.colour} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </ChartPanel>
  );
}
