// The one JS home of colour literals (docs/COLOURS.md). Roles copied from the
// AB2026 dashboard: teals for what households gain, ambers for what they lose,
// greys for no change and for the baseline or official figure.
export const CHART_COLOURS = {
  gain: "#319795",
  gainLight: "#81E6D9",
  loss: "#D97706",
  lossLight: "#FBBF24",
  noChange: "#9CA3AF",
  before: "#9CA3AF",
  after: "#319795",
  official: "#6B7280",
  zeroLine: "#374151",
  grid: "#E5E7EB",
  tick: "#6B7280",
  text: "#374151",
  surface: "#FFFFFF",
  highlight: "#285E61",
};

// Each modelled measure's colour, by position in the catalogue. Distinct from
// the gain (teal) and loss (amber) roles, so a measure's colour never reads
// as a gain or a loss.
export const MEASURE_RAMP = ["#2B6CB0", "#805AD5", "#4A5568", "#B83280"];

export function measureColour(index) {
  return MEASURE_RAMP[index % MEASURE_RAMP.length];
}

export const WINNERS_LOSERS_SERIES = [
  { key: "gain_more_5", label: "Gain more than 5%", colour: CHART_COLOURS.gain },
  { key: "gain_less_5", label: "Gain less than 5%", colour: CHART_COLOURS.gainLight },
  { key: "no_change", label: "No change", colour: CHART_COLOURS.noChange },
  { key: "lose_less_5", label: "Lose less than 5%", colour: CHART_COLOURS.lossLight },
  { key: "lose_more_5", label: "Lose more than 5%", colour: CHART_COLOURS.loss },
];
