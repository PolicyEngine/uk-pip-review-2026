import { formatMillions } from "../utils/measures";

export default function BaselineTab({ data }) {
  return (
    <div className="tab-body">
      <section className="panel">
        <h3 className="m-0 mb-1 text-lg font-semibold">PIP under current law</h3>
        <p className="m-0 mb-4 text-sm text-slate-500">
          DWP&apos;s spending and caseload forecast, England and Wales plus abroad. The modelled baseline is added once model figures are generated.
        </p>
        <div className="overflow-x-auto">
          <table className="data-table compact">
            <thead>
              <tr>
                <th>Year</th>
                <th>Spending</th>
                <th>Caseload</th>
              </tr>
            </thead>
            <tbody>
              {data.spending_path.map((row) => (
                <tr key={row.year}>
                  <td>{row.fiscal_year}</td>
                  <td>{formatMillions(row.dwp_m)}</td>
                  <td>{row.dwp_caseload_k ? `${(row.dwp_caseload_k / 1000).toFixed(2)}m` : "Not available"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="m-0 mt-4 text-sm text-slate-500">Source: DWP benefit expenditure and caseload tables, Spring Forecast 2026.</p>
      </section>
    </div>
  );
}
