import { measureColour } from "./chartTheme";

// The catalogue: every view reads the measure list from results.json, never
// from a hard-coded list, so a measure added to the registry shows everywhere.
// A measure has figures only when its budgetary_impact is present; a
// computable measure without them (a structural measure before a model run,
// or a withdrawn one) is listed but never drawn as £0.
export function hasFigures(m) {
  return Array.isArray(m.budgetary_impact) && m.status !== "withdrawn";
}

export function catalogue(data) {
  const withFigures = data.measures.filter(hasFigures);
  return data.measures.map((m) => ({
    ...m,
    hasFigures: hasFigures(m),
    colour: hasFigures(m) ? measureColour(withFigures.indexOf(m)) : null,
  }));
}

export const ROUTE_LABELS = {
  "dashboard-param": "Modelled: parameter change",
  "dashboard-structural": "Modelled: structural change",
  ledger: "Fiscal line only",
  "not-computable": "Not modelled with current data",
  "needs-pe-uk-first": "Not modelled: needs a model change first",
};

export const ROUTE_GROUPS = [
  { label: "Modelled", routes: ["dashboard-param", "dashboard-structural"] },
  { label: "Fiscal line only", routes: ["ledger"] },
  { label: "Not modelled", routes: ["not-computable", "needs-pe-uk-first"] },
];

export const IN_REPORT_LABELS = {
  yes: "Yes",
  no: "No",
  "not-yet-published": "Not yet published",
};

export function fiscalYear(year) {
  return `${year}-${String((year + 1) % 100).padStart(2, "0")}`;
}

export function formatMillions(value) {
  if (value === null || value === undefined) return "Not available";
  const sign = value < 0 ? "-" : "";
  const abs = Math.abs(value);
  if (abs >= 1000) return `${sign}£${(abs / 1000).toFixed(1)}bn`;
  return `${sign}£${Math.round(abs)}m`;
}

// One unit per axis: £bn when any value reaches £1bn, otherwise £m.
export function millionsAxis(values) {
  const max = Math.max(0, ...values.filter((v) => v !== null && v !== undefined).map((v) => Math.abs(v)));
  if (max >= 1000) return (v) => `${v < 0 ? "-" : ""}£${(Math.abs(v) / 1000).toFixed(1)}bn`;
  return (v) => `${v < 0 ? "-" : ""}£${Math.round(Math.abs(v))}m`;
}

export function formatPounds(value) {
  if (value === null || value === undefined) return "Withheld";
  const sign = value < 0 ? "-" : "";
  return `${sign}£${Math.abs(Math.round(value)).toLocaleString("en-GB")}`;
}

export function formatChange(value) {
  if (value === null || value === undefined) return "n/a";
  if (Math.abs(value) < 0.5) return "£0";
  return `${value > 0 ? "+" : "-"}£${Math.abs(Math.round(value)).toLocaleString("en-GB")}`;
}

// Totals by year for the selected measures. A missing cell stays null and is
// never summed as zero.
export function totalByYear(measures, years) {
  return years.map((year) => {
    const row = { year, fiscal_year: fiscalYear(year) };
    let total = 0;
    let complete = true;
    for (const m of measures) {
      const cell = m.budgetary_impact?.find((r) => r.year === year);
      const value = cell?.value_m ?? null;
      row[m.id] = value;
      if (value === null) complete = false;
      else total += value;
    }
    row.total = complete && measures.length ? total : null;
    return row;
  });
}

// The package entry when the selection is exactly the package's measures.
export function packageFor(data, selected) {
  const ids = data.package?.measure_ids;
  if (!ids || ids.length !== selected.length) return null;
  return ids.every((id) => selected.includes(id)) ? data.package : null;
}

export function toCsv(rows) {
  if (!rows.length) return "";
  const keys = Object.keys(rows[0]);
  const escape = (v) => (typeof v === "string" && /[",\n]/.test(v) ? `"${v.replaceAll('"', '""')}"` : v ?? "");
  return [keys.join(","), ...rows.map((r) => keys.map((k) => escape(r[k])).join(","))].join("\n");
}
