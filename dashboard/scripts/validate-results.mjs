// Build-time check of public/data/results.json, mirroring
// pip_review.publication.validate_public for what the page relies on:
// - status is placeholder, mock, provisional or final, with a banner for
//   every status except final, and MOCK in a mock banner;
// - a measure without figures is null, never zero;
// - on a provisional or final page, every public data file has a sign-off
//   row in data_inputs/public_data_review.csv with its current SHA-256.
import { createHash } from "node:crypto";
import { existsSync, readdirSync, readFileSync } from "node:fs";

const STATUSES = ["placeholder", "mock", "provisional", "final"];
const PLACEHOLDER_STATUSES = ["placeholder", "mock"];
const dataDir = new URL("../public/data/", import.meta.url);
const data = JSON.parse(readFileSync(new URL("results.json", dataDir)));
const errors = [];
for (const key of ["schema_version", "status", "years", "measures", "spending_path", "households", "basis", "engine"]) {
  if (!(key in data)) errors.push(`missing ${key}`);
}
if (!STATUSES.includes(data.status)) errors.push(`status ${data.status} is not one of ${STATUSES.join(", ")}`);
if (data.status !== "final" && !data.banner?.trim()) errors.push(`status ${data.status} needs banner text`);
if (data.status === "mock" && !data.banner?.includes("MOCK")) errors.push("a mock page's banner must contain MOCK");
if (data.measures?.some((m) => m.placeholder) && !PLACEHOLDER_STATUSES.includes(data.status)) {
  errors.push("placeholder measures need status placeholder or mock");
}
for (const m of data.measures ?? []) {
  const figures = m.computable && m.status !== "withdrawn";
  if (!figures && m.budgetary_impact !== null) errors.push(`${m.id}: no figures expected, but carries one`);
  if (figures && !PLACEHOLDER_STATUSES.includes(data.status) && !Array.isArray(m.budgetary_impact)) {
    errors.push(`${m.id}: modelled but has no figures`);
  }
}

if (["provisional", "final"].includes(data.status)) {
  const reviewPath = new URL("../../data_inputs/public_data_review.csv", import.meta.url);
  const rows = existsSync(reviewPath)
    ? readFileSync(reviewPath, "utf8").trim().split("\n").slice(1).map((line) => line.split(","))
    : [];
  for (const name of readdirSync(dataDir)) {
    const sha = createHash("sha256").update(readFileSync(new URL(name, dataDir))).digest("hex");
    const row = rows.find(([path]) => path === `dashboard/public/data/${name}`);
    if (!row) errors.push(`${name}: no sign-off row in data_inputs/public_data_review.csv`);
    else if (row[1] !== sha) errors.push(`${name}: sign-off row is for another version (SHA-256 differs)`);
    else if (!row[2]?.trim() || !row[3]?.trim()) errors.push(`${name}: sign-off row needs a reviewer and a date`);
  }
}
if (errors.length) {
  console.error(errors.join("\n"));
  process.exit(1);
}
console.log(`results.json ok: ${data.measures.length} measures, status ${data.status}`);
