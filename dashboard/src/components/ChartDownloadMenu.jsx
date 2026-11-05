import { toCsv } from "../utils/measures";

// CSV download for the rows behind a chart. The AB2026 menu also offers PNG,
// SVG and text; add them when the charts are final.
export default function ChartDownloadMenu({ rows, filename }) {
  const download = () => {
    const blob = new Blob([toCsv(rows)], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${filename}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };
  return (
    <button type="button" className="toggle-button" onClick={download} disabled={!rows?.length}>
      Download CSV
    </button>
  );
}
