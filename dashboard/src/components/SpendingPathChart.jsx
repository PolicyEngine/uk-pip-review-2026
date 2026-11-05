import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CHART_COLOURS } from "../utils/chartTheme";
import { formatMillions } from "../utils/measures";
import ChartPanel from "./ChartPanel";

// The "within OBR projections" test: the reformed path against the official one.
export default function SpendingPathChart({ path }) {
  return (
    <ChartPanel
      title="PIP spending against the official path"
      subtitle="England and Wales, £ million, nominal"
      rows={path}
      filename="spending-path"
      moreInfo="The official line is DWP's Spring Forecast 2026. The reformed line adds the selected measures' cost to it; in the template the measure costs are placeholders."
    >
      <div style={{ width: "100%", height: 320 }}>
        <ResponsiveContainer>
          <LineChart data={path}>
            <CartesianGrid stroke={CHART_COLOURS.grid} vertical={false} />
            <XAxis dataKey="fiscal_year" stroke={CHART_COLOURS.tick} />
            <YAxis tickFormatter={formatMillions} stroke={CHART_COLOURS.tick} width={70} domain={["auto", "auto"]} />
            <Tooltip formatter={(v) => formatMillions(v)} />
            <Legend />
            <Line isAnimationActive={false} dataKey="dwp_m" name="Official (DWP)" stroke={CHART_COLOURS.official} strokeDasharray="6 4" dot />
            <Line isAnimationActive={false} dataKey="reformed_m" name="With selected measures" stroke={CHART_COLOURS.after} dot />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </ChartPanel>
  );
}
