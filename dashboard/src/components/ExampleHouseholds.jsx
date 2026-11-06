import { fiscalYear, formatChange, formatPounds } from "../utils/measures";

// Preset households, precomputed by the pipeline. Placeholder mode gives PIP
// only (rate x 52); a model run adds net income, so the Universal Credit,
// Carer's Allowance and benefit cap knock-ons show. Not a calculator: there
// are no inputs.
function cell(h, m) {
  const r = h.reform[m.id];
  if (!r) return null;
  const net = r.net_income !== null && h.baseline.net_income !== null;
  return { change: net ? r.net_income - h.baseline.net_income : r.pip - h.baseline.pip, net };
}

export default function ExampleHouseholds({ households, measures, year }) {
  const shown = measures.filter((m) => m.hasFigures);
  const net = households.some((h) => h.baseline.net_income !== null);
  const what = net ? "household net income" : "PIP only, before any effect on other benefits";
  return (
    <div className="tab-body">
      <section className="panel">
        <h3 className="m-0 mb-1 text-lg font-semibold">Example households</h3>
        <p className="m-0 mb-4 text-sm text-slate-500">
          £ a year in {fiscalYear(year)}: {what} under current law, and the change under each measure.
        </p>
        {!households.length ? (
          <p className="m-0 text-sm text-slate-600">No example households in this run.</p>
        ) : (
          <>
            <div className="household-table overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Household</th>
                    <th>Current law</th>
                    {shown.map((m) => (
                      <th key={m.id}>{m.name}: £ change</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {households.map((h) => (
                    <tr key={h.id}>
                      <td>{h.label}</td>
                      <td>{formatPounds(net ? h.baseline.net_income : h.baseline.pip)}</td>
                      {shown.map((m) => (
                        <td key={m.id}>{formatChange(cell(h, m)?.change)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="household-cards" data-testid="household-cards">
              {households.map((h) => (
                <article key={h.id} className="metric-card">
                  <p className="m-0 font-semibold text-slate-800">{h.label}</p>
                  <p className="m-0 mt-1 text-sm text-slate-600">Current law: {formatPounds(net ? h.baseline.net_income : h.baseline.pip)}</p>
                  <ul className="m-0 mt-2 pl-0 text-sm">
                    {shown.map((m) => (
                      <li key={m.id} className="flex justify-between gap-3">
                        <span>{m.name}</span>
                        <strong>{formatChange(cell(h, m)?.change)}</strong>
                      </li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>
          </>
        )}
      </section>
    </div>
  );
}
