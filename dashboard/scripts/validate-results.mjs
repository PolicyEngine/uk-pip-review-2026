// Build-time check of public/data/results.json: the schema the page needs,
// and the placeholder banner while any measure is a placeholder.
import { readFileSync } from "node:fs";

const data = JSON.parse(readFileSync(new URL("../public/data/results.json", import.meta.url)));
const errors = [];
for (const key of ["schema_version", "status", "years", "measures", "spending_path", "households", "basis", "engine"]) {
  if (!(key in data)) errors.push(`missing ${key}`);
}
if (data.measures?.some((m) => m.placeholder) && (data.status !== "placeholder" || !data.banner)) {
  errors.push("placeholder measures need status 'placeholder' and banner text");
}
for (const m of data.measures ?? []) {
  if (!m.computable && m.budgetary_impact !== null) errors.push(`${m.id}: not computable but carries a figure`);
  if (m.computable && !Array.isArray(m.budgetary_impact)) errors.push(`${m.id}: computable but has no figures`);
}
if (errors.length) {
  console.error(errors.join("\n"));
  process.exit(1);
}
console.log(`results.json ok: ${data.measures.length} measures, status ${data.status}`);
