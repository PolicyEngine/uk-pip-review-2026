import { Bar, BarChart, CartesianGrid, Cell, Tooltip, XAxis, YAxis } from "recharts";
import useWidth from "../hooks/useWidth";
import { CHART_COLOURS } from "../utils/chartTheme";
import { fiscalYear, formatMillions, millionsAxis } from "../utils/measures";
import ChartBox from "./ChartBox";
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
  const phone = useWidth() < 640;
  const tick = millionsAxis(rows.flatMap((r) => [r.base, r.base + r.size]));
  const cells = rows.map((row) => (
    <Cell key={row.name} fill={row.net ? CHART_COLOURS.highlight : row.value >= 0 ? CHART_COLOURS.gain : CHART_COLOURS.loss} />
  ));
  const tooltip = <Tooltip formatter={(v, n, item) => (n === "size" ? formatMillions(item.payload.value) : null)} />;
  return (
    <ChartPanel title={`Cost by measure, ${fiscalYear(year)}`} subtitle="£ million; teal is a cost, amber a saving" rows={rows} filename="waterfall">
      <ChartBox height={phone ? 60 + rows.length * 56 : 320}>
        {phone ? (
          <BarChart data={rows} layout="vertical" margin={{ left: 8, right: 16 }}>
            <CartesianGrid stroke={CHART_COLOURS.grid} horizontal={false} />
            <XAxis type="number" tickFormatter={tick} stroke={CHART_COLOURS.tick} tick={{ fontSize: 11 }} />
            <YAxis type="category" dataKey="name" width={120} interval={0} stroke={CHART_COLOURS.tick} tick={{ fontSize: 11 }} />
            {tooltip}
            <Bar isAnimationActive={false} dataKey="base" stackId="w" fill="transparent" />
            <Bar isAnimationActive={false} dataKey="size" stackId="w">
              {cells}
            </Bar>
          </BarChart>
        ) : (
          <BarChart data={rows}>
            <CartesianGrid stroke={CHART_COLOURS.grid} vertical={false} />
            <XAxis dataKey="name" stroke={CHART_COLOURS.tick} interval={0} tick={{ fontSize: 12 }} />
            <YAxis tickFormatter={tick} stroke={CHART_COLOURS.tick} width={70} />
            {tooltip}
            <Bar isAnimationActive={false} dataKey="base" stackId="w" fill="transparent" />
            <Bar isAnimationActive={false} dataKey="size" stackId="w">
              {cells}
            </Bar>
          </BarChart>
        )}
      </ChartBox>
    </ChartPanel>
  );
}
