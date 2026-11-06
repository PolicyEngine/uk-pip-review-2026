import { ResponsiveContainer } from "recharts";

// A fixed-height box for one chart. initialDimension gives Recharts a size
// before the first measure, so it does not warn about width(-1).
export default function ChartBox({ height = 320, children }) {
  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer minWidth={0} initialDimension={{ width: 800, height }}>
        {children}
      </ResponsiveContainer>
    </div>
  );
}
