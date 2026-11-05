import { formatPounds } from "../utils/measures";

// Preset households, precomputed by the pipeline. In the template the values
// are PIP only (rates x weeks); the real calculator adds the UC and Carer's
// Allowance knock-ons from the full model.
export default function HouseholdCalculator({ households, measures }) {
  const computable = measures.filter((m) => m.computable);
  return (
    <div className="tab-body">
      <section className="panel">
        <h3 className="m-0 mb-1 text-lg font-semibold">Example households</h3>
        <p className="m-0 mb-4 text-sm text-slate-500">Annual PIP under current law and each modelled measure, 2027-28 rates held at 2026-27 values. Placeholder.</p>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Household</th>
                <th>Current law</th>
                {computable.map((m) => (
                  <th key={m.id}>{m.name}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {households.map((h) => (
                <tr key={h.id}>
                  <td>{h.label}</td>
                  <td>{formatPounds(h.baseline_pip)}</td>
                  {computable.map((m) => (
                    <td key={m.id}>{formatPounds(h.reform_pip[m.id])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
