import { formatMillions } from "../utils/measures";

export default function BaselineTab({ data }) {
  return (
    <div className="tab-body">
      <section className="panel">
        <h3 className="m-0 mb-1 text-lg font-semibold">PIP under current law</h3>
        <p className="m-0 mb-4 text-sm text-slate-500">Official spending and caseload path, England and Wales. The modelled baseline is added on the day.</p>
        <table className="data-table compact">
          <thead>
            <tr>
              <th>Year</th>
              <th>Official spending</th>
            </tr>
          </thead>
          <tbody>
            {data.spending_path.map((row) => (
              <tr key={row.year}>
                <td>{row.fiscal_year}</td>
                <td>{formatMillions(row.dwp_m)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="m-0 mt-4 text-sm text-slate-500">Source: DWP benefit expenditure and caseload tables, Spring Forecast 2026.</p>
      </section>
    </div>
  );
}
