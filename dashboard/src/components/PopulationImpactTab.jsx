import { useState } from "react";
import { fiscalYear, formatMillions, packageFor } from "../utils/measures";
import BudgetaryImpactChart from "./BudgetaryImpactChart";
import { AgeView, EntryPicker, PovertyView, RegionView } from "./BreakdownViews";
import DistributionalChart from "./DistributionalChart";
import EmptyState from "./EmptyState";
import PolicySelector from "./PolicySelector";
import SpendingPathChart from "./SpendingPathChart";
import StatTiles from "./StatTiles";
import ViewTabs from "./ViewTabs";
import WaterfallChart from "./WaterfallChart";
import WinnersLosersChart from "./WinnersLosersChart";

export const SUB_VIEWS = [
  { value: "cost", label: "Cost" },
  { value: "deciles", label: "By income decile" },
  { value: "winners", label: "Who gains and loses" },
  { value: "region", label: "By region" },
  { value: "age", label: "By age" },
  { value: "poverty", label: "Poverty" },
];

const PACKAGE_ID = "__package";

function peopleAffected(entry) {
  const p = entry?.people_affected;
  if (!p) return { value: "Not available", note: "Select one measure, or all once the package is modelled" };
  if (p.suppressed) return { value: "Withheld", note: "Too few survey households" };
  const k = (v) => (v >= 1000 ? `${(v / 1000).toFixed(2)}m` : `${Math.round(v)}k`);
  return { value: `${k(p.gain_k)} gain, ${k(p.lose_k)} lose`, note: "People whose PIP award changes" };
}

export default function PopulationImpactTab({ data, measures, selected, onSelect, sub, onSub, onOpenPolicies, onOpenMethod }) {
  const withFigures = measures.filter((m) => m.hasFigures);
  const chosen = withFigures.filter((m) => selected.includes(m.id));
  const pkg = packageFor(data, chosen.map((m) => m.id));
  const options = [
    ...(chosen.length > 1 ? [{ id: PACKAGE_ID, label: "All selected measures", ...(pkg ?? {}) }] : []),
    ...chosen.map((m) => ({ ...m, label: m.name })),
  ];
  const [entryId, setEntryId] = useState(PACKAGE_ID);
  const entry = options.find((o) => o.id === entryId) ?? options[0];
  const picker = options.length > 1 ? <EntryPicker options={options} active={entry} onChange={setEntryId} /> : null;
  const lastYear = data.years[data.years.length - 1];
  const net = chosen.reduce((sum, m) => sum + (m.budgetary_impact.find((r) => r.year === lastYear)?.value_m ?? 0), 0);
  const path = data.spending_path.map((row) => {
    const add = chosen.reduce((s, m) => s + (m.budgetary_impact.find((r) => r.year === row.year)?.value_m ?? 0), 0);
    return { ...row, reformed_m: row.dwp_m + add };
  });
  const notModelled = measures.filter((m) => !m.hasFigures).length;
  const single = chosen.length === 1 ? chosen[0] : pkg;
  const people = peopleAffected(single);
  return (
    <div className="tab-body">
      <PolicySelector measures={withFigures} selected={selected} onChange={onSelect} />
      <StatTiles
        tiles={[
          ...(chosen.length
            ? [
                { label: `Net cost, ${fiscalYear(lastYear)}`, value: formatMillions(net) },
                { label: "People affected", value: people.value, note: people.note },
              ]
            : []),
          {
            label: "Measures not shown here",
            value: String(notModelled),
            note: (
              <button type="button" className="underline" onClick={onOpenPolicies}>
                See the reason for each
              </button>
            ),
          },
        ]}
      />
      <ViewTabs views={SUB_VIEWS} active={sub} onChange={onSub} label="Population impact" sub />
      {!chosen.length ? (
        <EmptyState testId="select-measure">Select at least one measure above.</EmptyState>
      ) : (
        <>
          {sub === "cost" && (
            <>
              <BudgetaryImpactChart measures={chosen} years={data.years} onMethod={onOpenMethod} />
              <WaterfallChart measures={chosen} year={lastYear} />
              <SpendingPathChart path={path} />
            </>
          )}
          {sub === "deciles" && <DistributionalChart measures={chosen} onMethod={onOpenMethod} />}
          {sub === "winners" && <WinnersLosersChart options={options} active={entry?.id} onChange={setEntryId} />}
          {sub === "region" && <RegionView entry={entry} picker={picker} />}
          {sub === "age" && <AgeView entry={entry} picker={picker} />}
          {sub === "poverty" && <PovertyView entry={entry} picker={picker} />}
        </>
      )}
    </div>
  );
}
