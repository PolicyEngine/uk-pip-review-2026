import { CartesianGrid, Legend, Line, LineChart, Tooltip, XAxis, YAxis } from "recharts";
import { CHART_COLOURS } from "../utils/chartTheme";
import { formatMillions, millionsAxis } from "../utils/measures";
import ChartBox from "./ChartBox";
import ChartPanel from "./ChartPanel";

// The reformed path against the official one.
export default function SpendingPathChart({ path }) {
  const tick = millionsAxis(path.flatMap((r) => [r.dwp_m, r.reformed_m]));
  return (
    <ChartPanel
      title="PIP spending against the official path"
      subtitle="£ million, nominal; official path covers England and Wales plus abroad"
      rows={path}
      filename="spending-path"
      moreInfo="The official line is DWP's forecast (see the Baseline tab). The other line adds the selected measures' cost to it."
    >
      <ChartBox>
        <LineChart data={path} margin={{ left: 8, right: 28 }}>
          <CartesianGrid stroke={CHART_COLOURS.grid} vertical={false} />
          <XAxis dataKey="fiscal_year" stroke={CHART_COLOURS.tick} interval={0} tick={{ fontSize: 12 }} padding={{ left: 12, right: 12 }} />
          <YAxis tickFormatter={tick} stroke={CHART_COLOURS.tick} width={70} domain={["auto", "auto"]} tickCount={5} />
          <Tooltip formatter={(v) => formatMillions(v)} />
          <Legend />
          <Line isAnimationActive={false} dataKey="dwp_m" name="Official (DWP)" stroke={CHART_COLOURS.official} strokeDasharray="6 4" dot />
          <Line isAnimationActive={false} dataKey="reformed_m" name="With selected measures" stroke={CHART_COLOURS.highlight} dot />
        </LineChart>
      </ChartBox>
    </ChartPanel>
  );
}
