import { Bar, BarChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CHART_COLOURS } from "../utils/chartTheme";
import { formatMillions, totalByYear } from "../utils/measures";
import ChartPanel from "./ChartPanel";

export default function BudgetaryImpactChart({ measures, years, basis }) {
  const rows = totalByYear(measures, years);
  return (
    <ChartPanel
      title="Cost by year"
      subtitle={basis}
      rows={rows}
      filename="cost-by-year"
      moreInfo="Each bar stacks the selected measures. Measures that are not computable are listed on the Policies tab and are not shown as zero."
    >
      <div style={{ width: "100%", height: 320 }}>
        <ResponsiveContainer>
          <BarChart data={rows}>
            <CartesianGrid stroke={CHART_COLOURS.grid} vertical={false} />
            <XAxis dataKey="year" tickFormatter={(y) => `${y}-${String((y + 1) % 100).padStart(2, "0")}`} stroke={CHART_COLOURS.tick} />
            <YAxis tickFormatter={formatMillions} stroke={CHART_COLOURS.tick} width={70} />
            <Tooltip formatter={(v) => formatMillions(v)} />
            <ReferenceLine y={0} stroke={CHART_COLOURS.zeroLine} />
            {measures.map((m) => (
              <Bar isAnimationActive={false} key={m.id} dataKey={m.id} name={m.name} stackId="cost" fill={m.colour} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </ChartPanel>
  );
}
