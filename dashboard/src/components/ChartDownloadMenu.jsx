import { downloadPng, downloadSvg, saveBlob } from "../utils/chartExport";
import { toCsv } from "../utils/measures";

// Downloads for one chart: the rows behind it as CSV, and the drawn chart
// as SVG or PNG.
export default function ChartDownloadMenu({ rows, filename, title, chartRef }) {
  const csv = () => saveBlob(new Blob([toCsv(rows)], { type: "text/csv" }), `${filename}.csv`);
  return (
    <div className="flex gap-2" role="group" aria-label="Download">
      <button type="button" className="toggle-button" onClick={csv} disabled={!rows?.length}>
        CSV
      </button>
      <button type="button" className="toggle-button" onClick={() => downloadSvg(chartRef?.current, title, filename)}>
        SVG
      </button>
      <button type="button" className="toggle-button" onClick={() => downloadPng(chartRef?.current, title, filename)}>
        PNG
      </button>
    </div>
  );
}
