import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CHART_COLOURS, WINNERS_LOSERS_SERIES } from "../utils/chartTheme";
import ChartPanel from "./ChartPanel";

export default function WinnersLosersChart({ measure }) {
  const rows = measure?.winners_losers ?? [];
  return (
    <ChartPanel
      title={`Who gains and who loses: ${measure?.name ?? ""}`}
      subtitle="Share of people by household income decile, %"
      rows={rows}
      filename="winners-losers"
    >
      <div style={{ width: "100%", height: 360 }}>
        <ResponsiveContainer>
          <BarChart data={rows} layout="vertical">
            <CartesianGrid stroke={CHART_COLOURS.grid} horizontal={false} />
            <XAxis type="number" domain={[0, 100]} stroke={CHART_COLOURS.tick} />
            <YAxis type="category" dataKey="decile" stroke={CHART_COLOURS.tick} width={30} interval={0} />
            <Tooltip formatter={(v) => `${v}%`} />
            <Legend />
            {WINNERS_LOSERS_SERIES.map((s) => (
              <Bar isAnimationActive={false} key={s.key} dataKey={s.key} name={s.label} stackId="wl" fill={s.colour} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </ChartPanel>
  );
}
