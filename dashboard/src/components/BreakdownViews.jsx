import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, Tooltip, XAxis, YAxis } from "recharts";
import { CHART_COLOURS } from "../utils/chartTheme";
import { formatMillions, formatPounds } from "../utils/measures";
import ChartBox from "./ChartBox";
import ChartPanel from "./ChartPanel";
import EmptyState from "./EmptyState";

const REGION_LABELS = {
  NORTH_EAST: "North East",
  NORTH_WEST: "North West",
  YORKSHIRE: "Yorkshire and the Humber",
  EAST_MIDLANDS: "East Midlands",
  WEST_MIDLANDS: "West Midlands",
  EAST_OF_ENGLAND: "East of England",
  LONDON: "London",
  SOUTH_EAST: "South East",
  SOUTH_WEST: "South West",
  WALES: "Wales",
};

const MODEL_RUN_ONLY = "Shown once a model run has produced this table.";

export function EntryPicker({ options, active, onChange }) {
  return (
    <div className="pill-row" role="group" aria-label="Measure">
      {options.map((o) => (
        <button key={o.id} type="button" className={`pill ${active?.id === o.id ? "active" : ""}`} aria-pressed={active?.id === o.id} onClick={() => onChange(o.id)}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

function signColour(value) {
  return value === null ? CHART_COLOURS.noChange : value >= 0 ? CHART_COLOURS.gain : CHART_COLOURS.loss;
}

function ChangeBars({ rows, labelKey, valueKey, height = 360 }) {
  return (
    <ChartBox height={height}>
      <BarChart data={rows} layout="vertical" margin={{ left: 8, right: 16 }}>
        <CartesianGrid stroke={CHART_COLOURS.grid} horizontal={false} />
        <XAxis type="number" tickFormatter={formatPounds} stroke={CHART_COLOURS.tick} tick={{ fontSize: 11 }} />
        <YAxis type="category" dataKey={labelKey} width={150} interval={0} stroke={CHART_COLOURS.tick} tick={{ fontSize: 12 }} />
        <Tooltip formatter={(v) => formatPounds(v)} />
        <ReferenceLine x={0} stroke={CHART_COLOURS.zeroLine} />
        <Bar isAnimationActive={false} dataKey={valueKey} name="Average change">
          {rows.map((r) => (
            <Cell key={r[labelKey]} fill={signColour(r[valueKey])} />
          ))}
        </Bar>
      </BarChart>
    </ChartBox>
  );
}

function withheldNote(rows, labelKey) {
  const names = rows.filter((r) => r.suppressed).map((r) => r[labelKey]);
  return names.length ? <p className="m-0 mt-2 text-sm text-slate-600">Withheld: too few survey households in {names.join(", ")}.</p> : null;
}

export function RegionView({ entry, picker }) {
  const rows = (entry?.by_region ?? []).map((r) => ({ ...r, name: REGION_LABELS[r.region] ?? r.region }));
  return (
    <ChartPanel title="By region" subtitle="£ a year, average change per household, England and Wales" rows={rows.length ? rows : null} filename="by-region">
      {picker}
      {rows.length ? <ChangeBars rows={rows} labelKey="name" valueKey="avg_change_gbp" /> : <EmptyState>{MODEL_RUN_ONLY}</EmptyState>}
      {withheldNote(rows, "name")}
      <p className="m-0 mt-3 text-sm text-slate-600" data-testid="scotland-note">
        Scotland has Adult Disability Payment and Northern Ireland its own PIP, so neither is shown. Any change to Scotland&apos;s block grant from these measures is not estimated here.
      </p>
    </ChartPanel>
  );
}

export function AgeView({ entry, picker }) {
  const rows = (entry?.by_age ?? []).map((r) => ({ ...r, name: `Aged ${r.age_band}` }));
  return (
    <ChartPanel title="By age" subtitle="£ a year, average change in the household income of people in each age group" rows={rows.length ? rows : null} filename="by-age">
      {picker}
      {rows.length ? <ChangeBars rows={rows} labelKey="name" valueKey="avg_household_change_gbp" height={240} /> : <EmptyState>{MODEL_RUN_ONLY}</EmptyState>}
      {withheldNote(rows, "name")}
    </ChartPanel>
  );
}

export function PovertyView({ entry, picker }) {
  const poverty = entry?.poverty;
  const knock = entry?.knock_ons;
  return (
    <ChartPanel title="Poverty and knock-on effects" subtitle="People in England and Wales, relative poverty">
      {picker}
      {poverty ? (
        <table className="data-table compact">
          <thead>
            <tr>
              <th>Measure of poverty</th>
              <th>Current law</th>
              <th>Change, percentage points</th>
            </tr>
          </thead>
          <tbody>
            {[
              ["bhc", "Before housing costs"],
              ["ahc", "After housing costs"],
            ].map(([key, label]) => (
              <tr key={key}>
                <td>{label}</td>
                <td>{poverty[key].baseline_pct.toFixed(1)}%</td>
                <td>{poverty[key].change_pp > 0 ? "+" : ""}{poverty[key].change_pp.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <EmptyState>{MODEL_RUN_ONLY}</EmptyState>
      )}
      {knock && (
        <p className="m-0 mt-3 text-sm text-slate-700">
          Change in Carer&apos;s Allowance paid: {formatMillions(knock.carers_allowance_m)} a year. The model does not link Carer&apos;s Allowance to the cared-for person&apos;s award (see Methodology), so this stays near zero.
        </p>
      )}
    </ChartPanel>
  );
}

