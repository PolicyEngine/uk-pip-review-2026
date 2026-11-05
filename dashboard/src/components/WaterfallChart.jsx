import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CHART_COLOURS } from "../utils/chartTheme";
import { formatMillions } from "../utils/measures";
import ChartPanel from "./ChartPanel";

// Expansions against offsets in one year, ending at the net total. A cost to
// the Exchequer (households gain) is teal; a saving (households lose) is amber.
export function waterfallRows(measures, year) {
  let running = 0;
  const rows = measures.map((m) => {
    const value = m.budgetary_impact?.find((r) => r.year === year)?.value_m ?? 0;
    const start = running;
    running += value;
    return { name: m.name, base: Math.min(start, running), size: Math.abs(value), value };
  });
  rows.push({ name: "Net", base: Math.min(0, running), size: Math.abs(running), value: running, net: true });
  return rows;
}

export default function WaterfallChart({ measures, year }) {
  const rows = waterfallRows(measures, year);
  return (
    <ChartPanel title={`Cost by measure, ${year}-${String((year + 1) % 100).padStart(2, "0")}`} rows={rows} filename="waterfall">
      <div style={{ width: "100%", height: 320 }}>
        <ResponsiveContainer>
          <BarChart data={rows}>
            <CartesianGrid stroke={CHART_COLOURS.grid} vertical={false} />
            <XAxis dataKey="name" stroke={CHART_COLOURS.tick} interval={0} tick={{ fontSize: 12 }} />
            <YAxis tickFormatter={formatMillions} stroke={CHART_COLOURS.tick} width={70} />
            <Tooltip formatter={(v, n, item) => (n === "size" ? formatMillions(item.payload.value) : null)} />
            <Bar isAnimationActive={false} dataKey="base" stackId="w" fill="transparent" />
            <Bar isAnimationActive={false} dataKey="size" stackId="w">
              {rows.map((row) => (
                <Cell key={row.name} fill={row.net ? CHART_COLOURS.highlight : row.value >= 0 ? CHART_COLOURS.gain : CHART_COLOURS.loss} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </ChartPanel>
  );
}
