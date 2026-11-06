import { CHART_COLOURS } from "./chartTheme";

// SVG and PNG downloads of a drawn chart: the chart's own <svg>, with a
// title above it, on a white background. A cut-down version of the AB2026
// dashboard's exportChartAsSvg and rasteriseSvg.
const TITLE_HEIGHT = 36;

export function chartSvgText(container, title) {
  const svg = container?.querySelector("svg.recharts-surface");
  if (!svg) return null;
  const { width, height } = svg.getBoundingClientRect();
  const clone = svg.cloneNode(true);
  clone.setAttribute("x", "0");
  clone.setAttribute("y", String(TITLE_HEIGHT));
  const ns = "http://www.w3.org/2000/svg";
  const escape = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  const total = height + TITLE_HEIGHT;
  const body = new XMLSerializer().serializeToString(clone);
  const text = `<svg xmlns="${ns}" width="${width}" height="${total}" viewBox="0 0 ${width} ${total}" font-family="Inter, Arial, sans-serif"><rect width="100%" height="100%" fill="${CHART_COLOURS.surface}"/><text x="8" y="24" font-size="16" font-weight="600" fill="${CHART_COLOURS.text}">${escape(title)}</text>${body}</svg>`;
  return { text, width, height: total };
}

function save(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export function downloadSvg(container, title, filename) {
  const built = chartSvgText(container, title);
  if (built) save(new Blob([built.text], { type: "image/svg+xml" }), `${filename}.svg`);
}

export function downloadPng(container, title, filename, scale = 2) {
  const built = chartSvgText(container, title);
  if (!built) return;
  const image = new Image();
  image.onload = () => {
    const canvas = document.createElement("canvas");
    canvas.width = built.width * scale;
    canvas.height = built.height * scale;
    const context = canvas.getContext("2d");
    context.scale(scale, scale);
    context.drawImage(image, 0, 0);
    canvas.toBlob((blob) => blob && save(blob, `${filename}.png`), "image/png");
  };
  image.src = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(built.text)}`;
}

export { save as saveBlob };
