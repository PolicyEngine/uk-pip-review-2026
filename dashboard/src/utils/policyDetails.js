// Card text for each measure, keyed by id. A card is used only while the
// measure's description in results.json still matches `description`, so a
// stale card is ignored rather than shown against a changed measure.
export const POLICY_DETAILS = {
  standard_daily_living_rate: {
    description:
      "Illustrative: standard daily living 5% above its current-law rate in each year from 2027-28.",
    whoIsAffected: "People with the standard rate of the daily living component.",
    howItWorks: "Raises one weekly rate. No one moves between award levels.",
  },
  cost_category_tiers: {
    description:
      "Illustrative stand-in for awards set by cost categories: the standard daily living rate £8.30 a week above current law and the enhanced rate £4.60 a week below it. The values are placeholders, not a proposal.",
    whoIsAffected: "Everyone with a daily living award: standard gains, enhanced loses.",
    howItWorks: "Changes two weekly rates. Non-cash support is not modelled.",
  },
};

export function detailsFor(measure) {
  const details = POLICY_DETAILS[measure.id];
  if (!details || details.description !== measure.description) return null;
  return details;
}
