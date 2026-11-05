import { formatMillions } from "../utils/measures";
import BudgetaryImpactChart from "./BudgetaryImpactChart";
import DistributionalChart from "./DistributionalChart";
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
];

export default function PopulationImpactTab({ data, measures, selected, onSelect, sub, onSub, onOpenPolicies }) {
  const computable = measures.filter((m) => m.computable);
  const chosen = computable.filter((m) => selected.includes(m.id));
  const lastYear = data.years[data.years.length - 1];
  const net = chosen.reduce(
    (sum, m) => sum + (m.budgetary_impact.find((r) => r.year === lastYear)?.value_m ?? 0),
    0,
  );
  const path = data.spending_path.map((row) => {
    const add = chosen.reduce((s, m) => s + (m.budgetary_impact.find((r) => r.year === row.year)?.value_m ?? 0), 0);
    return { ...row, reformed_m: row.dwp_m + add };
  });
  const notComputable = measures.filter((m) => !m.computable).length;
  return (
    <div className="tab-body">
      <PolicySelector measures={computable} selected={selected} onChange={onSelect} />
      <StatTiles
        tiles={[
          { label: `Net cost, ${lastYear}-${String((lastYear + 1) % 100).padStart(2, "0")}`, value: formatMillions(net), note: "Placeholder" },
          { label: "Measures modelled", value: String(computable.length), note: "Placeholder parameter changes" },
          {
            label: "Measures not modelled",
            value: String(notComputable),
            note: (
              <button type="button" className="underline" onClick={onOpenPolicies}>
                See the reason for each
              </button>
            ),
          },
        ]}
      />
      <ViewTabs views={SUB_VIEWS} active={sub} onChange={onSub} label="Population impact" sub />
      {sub === "cost" && (
        <>
          <BudgetaryImpactChart measures={chosen} years={data.years} basis={data.basis.cost} />
          <WaterfallChart measures={chosen} year={lastYear} />
          <SpendingPathChart path={path} />
        </>
      )}
      {sub === "deciles" && <DistributionalChart measures={chosen} basis={data.basis.distribution} />}
      {sub === "winners" && <WinnersLosersChart measure={chosen[0] ?? computable[0]} />}
    </div>
  );
}
