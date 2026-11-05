import { measureColour } from "./chartTheme";

// The catalogue: every view reads the measure list from results.json, never
// from a hard-coded list, so a measure added to the registry shows everywhere.
export function catalogue(data) {
  const computable = data.measures.filter((m) => m.computable);
  return data.measures.map((m) => ({
    ...m,
    colour: m.computable ? measureColour(computable.indexOf(m)) : null,
  }));
}

export const ROUTE_LABELS = {
  "dashboard-param": "Modelled: parameter change",
  "dashboard-structural": "Modelled: structural change",
  ledger: "Fiscal line only",
  "not-computable": "Not computable with current data",
  "needs-pe-uk-first": "Needs a model change first",
};

export const LIKELIHOOD_LABELS = { high: "High", medium: "Medium", low: "Low" };

export function formatMillions(value) {
  if (value === null || value === undefined) return "Not computable";
  const sign = value < 0 ? "-" : "";
  const abs = Math.abs(value);
  if (abs >= 1000) return `${sign}£${(abs / 1000).toFixed(1)}bn`;
  return `${sign}£${Math.round(abs)}m`;
}

export function formatPounds(value) {
  if (value === null || value === undefined) return "n/a";
  return `£${Math.round(value).toLocaleString("en-GB")}`;
}

export function totalByYear(measures, years) {
  return years.map((year) => {
    const row = { year };
    for (const m of measures) {
      const cell = m.budgetary_impact?.find((r) => r.year === year);
      row[m.id] = cell ? cell.value_m : 0;
    }
    row.total = measures.reduce((sum, m) => sum + row[m.id], 0);
    return row;
  });
}

export function toCsv(rows) {
  if (!rows.length) return "";
  const keys = Object.keys(rows[0]);
  const escape = (v) => (typeof v === "string" && /[",\n]/.test(v) ? `"${v.replaceAll('"', '""')}"` : v ?? "");
  return [keys.join(","), ...rows.map((r) => keys.map((k) => escape(r[k])).join(","))].join("\n");
}
