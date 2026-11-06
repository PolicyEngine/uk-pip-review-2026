import { Bar, BarChart, CartesianGrid, ReferenceLine, Tooltip, XAxis, YAxis } from "recharts";
import useWidth from "../hooks/useWidth";
import { CHART_COLOURS } from "../utils/chartTheme";
import { formatMillions, millionsAxis, totalByYear } from "../utils/measures";
import ChartBox from "./ChartBox";
import ChartPanel from "./ChartPanel";
import MeasureKey from "./MeasureKey";

export default function BudgetaryImpactChart({ measures, years, onMethod }) {
  const rows = totalByYear(measures, years);
  const phone = useWidth() < 640;
  const tick = millionsAxis(rows.flatMap((r) => [r.total, ...measures.map((m) => r[m.id])]));
  return (
    <ChartPanel
      title="Cost by year"
      subtitle="£ million, cost to the Exchequer"
      onMethod={onMethod}
      rows={rows}
      filename="cost-by-year"
      moreInfo="Each bar stacks the selected measures. Measures that are not modelled are listed on the Policies tab and are not shown as zero."
    >
      <ChartBox>
        <BarChart data={rows} stackOffset="sign" margin={{ bottom: phone ? 24 : 4 }}>
          <CartesianGrid stroke={CHART_COLOURS.grid} vertical={false} />
          <XAxis
            dataKey="fiscal_year"
            stroke={CHART_COLOURS.tick}
            interval={0}
            angle={phone ? -35 : 0}
            textAnchor={phone ? "end" : "middle"}
            tick={{ fontSize: phone ? 11 : 13 }}
          />
          <YAxis tickFormatter={tick} stroke={CHART_COLOURS.tick} width={70} />
          <Tooltip formatter={(v) => formatMillions(v)} />
          <ReferenceLine y={0} stroke={CHART_COLOURS.zeroLine} />
          {measures.map((m) => (
            <Bar isAnimationActive={false} key={m.id} dataKey={m.id} name={m.name} stackId="cost" fill={m.colour} />
          ))}
        </BarChart>
      </ChartBox>
      <MeasureKey measures={measures} />
    </ChartPanel>
  );
}
