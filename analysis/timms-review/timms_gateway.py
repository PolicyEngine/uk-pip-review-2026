#!/usr/bin/env python3
"""PIP daily living as the single route to the UC health (LCWRA) element,
2029-30, for PolicyEngine's post on the Timms Review of PIP.

Three versions, each rewriting the UC health element after PolicyEngine UK's
UC rebalancing step (static, otherwise current law):
  full        every award needs a claimant on PIP daily living;
  new_claims  only awards at the new-claimant rate need one; protected-rate
              awards keep the element;
  protected   every existing award keeps the element.
In all three, awards with a claimant on PIP daily living but no element gain
it at the new-claimant rate (£217.26 a month in 2029-30). LCWRA status is
unchanged. Also writes a current-law PIP profile.

Disclosure floor: a published figure needs at least 3 survey households.

Run from a checkout of PolicyEngine/uk-milburn-review-dashboard (it uses
that repo's simulation builder and survey-household mapping), with
MILBURN_DASHBOARD pointing at it:
    MILBURN_DASHBOARD=/path/to/uk-milburn-review-dashboard \
        /path/to/uk-milburn-review-dashboard/.venv/bin/python timms_gateway.py
"""
import json, os, sys
from pathlib import Path
ROOT = Path(os.environ.get("MILBURN_DASHBOARD", "../uk-milburn-review-dashboard")).resolve()
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
from milburn_one_off_figures import release_lock, take_lock  # noqa: E402
Y = 2029; FLOOR = 3
OUT = Path(__file__).parent / "results" / "timms_gateway_raw.json"


def make_modifier(version):
    def modifier(sim):
        import numpy as np
        from policyengine_core.periods import period as as_period
        from policyengine_uk.utils.supplied_inputs import set_model_value
        from policyengine_uk.utils.uc_work_related_requirements import other_member_of_single_claim
        person = sim.populations["person"]; benunit = sim.populations["benunit"]
        per = as_period(Y)
        element = np.array(sim.calculate("uc_LCWRA_element", Y))
        claimant = person("is_uc_assessed_claimant", per) & ~other_member_of_single_claim(person, per)
        pip_dl = np.asarray(sim.calculate("pip_dl", Y)) > 0
        passes = np.asarray(benunit.any(claimant & pip_dl))
        new_rate = sim.tax_benefit_system.parameters.gov.dwp.universal_credit.rebalancing.new_claimant_health_element(f"{Y}-04-01") * 12
        has = element > 0
        gain = np.where(~has & passes, new_rate, 0.0)
        if version == "protected":
            new = np.where(has, element, gain)
        elif version == "full":
            new = np.where(has, np.where(passes, element, 0.0), gain)
        elif version == "new_claims":
            new_claim = np.asarray(sim.calculate("uc_receives_new_claimant_health_element", Y), dtype=bool)
            new = np.where(has, np.where(passes | ~new_claim, element, 0.0), gain)
        set_model_value(sim, "uc_LCWRA_element", Y, new)
        return sim
    return modifier


def main():
    import numpy as np
    for n in ("HUGGING_FACE_TOKEN", "HF_TOKEN", "HUGGINGFACE_HUB_TOKEN"):
        os.environ.pop(n, None)
    from uk_budget_data import local_build
    from uk_budget_data.models import DataConfig, Reform
    from uk_budget_data.pipeline import build_microsimulation, scatter_survey_households
    from uk_budget_data.reforms import get_reform
    from policyengine_core.periods import period as as_period
    from policyengine_uk.utils.uc_work_related_requirements import other_member_of_single_claim
    local_build.check_engine(); local_build.check_dataset()
    take_lock()
    out = {"build": local_build.LABEL, "year": Y}
    try:
        config = DataConfig(); path = str(config.dataset_path) if config.dataset_path else None
        pkg = get_reform("milburn_report_package")
        base = build_microsimulation(path, pkg.baseline_scenario_for(config))
        c = lambda s, v, m=None: np.asarray(s.calculate(v, Y, map_to=m) if m else s.calculate(v, Y))
        survey = np.asarray(scatter_survey_households(base, path))
        hid_h = c(base, "household_id"); hid_p = c(base, "household_id", "person")
        idx = {h: i for i, h in enumerate(hid_h)}
        p2h = np.array([idx[h] for h in hid_p])
        bid_b = c(base, "benunit_id"); bid_p = c(base, "benunit_id", "person")
        first = {}
        for i, bb in enumerate(bid_p):
            first.setdefault(bb, p2h[i])
        b2h = np.array([first[bb] for bb in bid_b])
        svp, svb = survey[p2h], survey[b2h]
        pw = c(base, "person_weight").astype(float); hw = c(base, "household_weight").astype(float); bw = c(base, "benunit_weight").astype(float)
        age = c(base, "age").astype(float); child = c(base, "is_child").astype(bool)
        bper = base.populations["person"]; per = as_period(Y)
        claimant = np.asarray(bper("is_uc_assessed_claimant", per) & ~other_member_of_single_claim(bper, per))
        lcwra = c(base, "uc_limited_capability_for_WRA").astype(bool)
        pipdl = c(base, "pip_dl").astype(float) > 0; pipm = c(base, "pip_m").astype(float) > 0
        country = c(base, "country", "person").astype(str)
        couple_b = c(base, "is_couple").astype(bool); kids_b = c(base, "benunit_count_children").astype(float) > 0
        couple_p = c(base, "is_couple", "person").astype(bool); kids_p = c(base, "benunit_count_children", "person").astype(float) > 0
        b = {k: c(base, k).astype(float) for k in ("household_net_income",)}
        b_uc_b = c(base, "universal_credit").astype(float); b_el_b = c(base, "uc_LCWRA_element").astype(float)
        b_cap_b = c(base, "benefit_cap_reduction").astype(float)
        b_uc_p = c(base, "universal_credit", "person").astype(float); b_el_p = c(base, "uc_LCWRA_element", "person").astype(float)
        b_pov = {k: c(base, k).astype(bool) for k in ("in_poverty_bhc", "in_poverty_ahc")}
        decile = c(base, "household_income_decile").astype(float)
        tot = float(pw.sum()); tot_child = float(pw[child].sum())

        def cell_p(mask):
            n = len(set(svp[mask])); return {"value": float(pw[mask].sum()) if n >= FLOOR else None, "n": int(n)}
        def cell_b_sum(vals, mask):
            n = len(set(svb[mask])); return {"value": float((vals * bw)[mask].sum()) if n >= FLOOR else None, "n": int(n)}
        def cell_b_mean(vals, mask):
            n = len(set(svb[mask])); return {"value": float((vals * bw)[mask].sum() / bw[mask].sum()) if n >= FLOOR and bw[mask].sum() > 0 else None, "n": int(n)}

        # Baseline PIP profile
        dlcat = c(base, "pip_dl_category").astype(str); mcat = c(base, "pip_m_category").astype(str)
        dl_amt = c(base, "pip_dl").astype(float); m_amt = c(base, "pip_m").astype(float)
        inwork = c(base, "in_work").astype(bool); wa = (age >= 16) & (age < 66)
        dec_p = decile[p2h]; uc_b_p = b_uc_p > 0; pov_p = b_pov["in_poverty_bhc"][p2h]
        anyp = pipdl | pipm
        prof = {"recipients_any": cell_p(anyp), "recipients_dl": cell_p(pipdl), "recipients_m": cell_p(pipm),
                "spend_dl_bn": float((dl_amt * pw).sum() / 1e9), "spend_m_bn": float((m_amt * pw).sum() / 1e9),
                "dl_by_category": {k: cell_p(dlcat == k) for k in sorted(set(dlcat))},
                "m_by_category": {k: cell_p(mcat == k) for k in sorted(set(mcat))},
                "working_age_recipients": cell_p(anyp & wa), "working_age_in_work": cell_p(anyp & wa & inwork),
                "recipients_on_uc": cell_p(anyp & uc_b_p), "recipients_in_abs_poverty_bhc": cell_p(anyp & pov_p),
                "by_decile": {int(d): cell_p(anyp & (dec_p == d)) for d in range(1, 11)},
                "by_country": {k: cell_p(anyp & (country == k)) for k in sorted(set(country))}}
        out["pip_profile"] = prof; print("profile", json.dumps(prof), flush=True)

        for version in ("full", "protected", "new_claims"):
            r = Reform(id=f"timms_{version}", name=version, description=version, simulation_modifier=make_modifier(version))
            sim = build_microsimulation(path, r.to_scenario())
            uc_b = c(sim, "universal_credit").astype(float); el_b = c(sim, "uc_LCWRA_element").astype(float)
            cap_b = c(sim, "benefit_cap_reduction").astype(float)
            uc_p = c(sim, "universal_credit", "person").astype(float); el_p = c(sim, "uc_LCWRA_element", "person").astype(float)
            net = c(sim, "household_net_income").astype(float); dnet = net - b["household_net_income"]
            pov = {k: c(sim, k).astype(bool) for k in ("in_poverty_bhc", "in_poverty_ahc")}
            lose_b = (el_b < b_el_b - 0.5) & (uc_b < b_uc_b - 0.5)
            gain_b = (el_b > b_el_b + 0.5) & (uc_b > b_uc_b + 0.5)
            lose_p = (el_p < b_el_p - 0.5) & (uc_p < b_uc_p - 0.5)
            gain_p = (el_p > b_el_p + 0.5) & (uc_p > b_uc_p + 0.5)
            lc = lose_p & claimant & lcwra & ~pipdl
            gc = gain_p & claimant & pipdl
            res = {
                "uc_change_bn": float(((uc_b - b_uc_b) * bw).sum() / 1e9),
                "net_income_change_bn": float((dnet * hw).sum() / 1e9),
                "benefit_cap_reduction_change_bn": float(((cap_b - b_cap_b) * bw).sum() / 1e9),
                "benunits_newly_capped": cell_b_sum(np.ones_like(bw), (cap_b > 0.5) & (b_cap_b <= 0.5)),
                "benunits_losing": cell_b_sum(np.ones_like(bw), lose_b),
                "benunits_gaining": cell_b_sum(np.ones_like(bw), gain_b),
                "benunits_gaining_new_uc_award": cell_b_sum(np.ones_like(bw), gain_b & (b_uc_b <= 0.5)),
                "avg_uc_loss_per_losing_benunit": cell_b_mean(b_uc_b - uc_b, lose_b),
                "avg_uc_gain_per_gaining_benunit": cell_b_mean(uc_b - b_uc_b, gain_b),
                "claimants_losing": cell_p(lc), "claimants_gaining": cell_p(gc),
                "losing_16_24": cell_p(lc & (age >= 16) & (age <= 24)),
                "losing_25_49": cell_p(lc & (age >= 25) & (age <= 49)),
                "losing_50_plus": cell_p(lc & (age >= 50)),
                "gaining_16_24": cell_p(gc & (age >= 16) & (age <= 24)),
                "losing_pip_mobility_only": cell_p(lc & pipm), "losing_no_pip": cell_p(lc & ~pipm),
                "losing_single_no_children": cell_p(lc & ~couple_p & ~kids_p), "losing_single_with_children": cell_p(lc & ~couple_p & kids_p),
                "losing_couple_no_children": cell_p(lc & couple_p & ~kids_p), "losing_couple_with_children": cell_p(lc & couple_p & kids_p),
                "losing_by_country": {k: cell_p(lc & (country == k)) for k in sorted(set(country))},
                "people_hh_worse": cell_p(dnet[p2h] < -1), "people_hh_better": cell_p(dnet[p2h] > 1),
                "better_off_not_gaining_element_benunit": cell_p((dnet[p2h] > 1) & ~gain_p),
            }
            for k in ("in_poverty_bhc", "in_poverty_ahc"):
                d0 = b_pov[k][p2h]; d1 = pov[k][p2h]; ch = d0 != d1
                n = len(set(svp[ch])); nc = len(set(svp[ch & child]))
                res[k] = {"people": float(pw[d1].sum() - pw[d0].sum()), "pp": 100 * float(pw[d1].sum() - pw[d0].sum()) / tot, "n": int(n),
                          "children": float(pw[d1 & child].sum() - pw[d0 & child].sum()), "children_pp": 100 * float(pw[d1 & child].sum() - pw[d0 & child].sum()) / tot_child, "n_children": int(nc)}
            res["deciles"] = {int(d): {"avg": float((dnet * hw)[decile == d].sum() / hw[decile == d].sum()), "n": int(len(set(survey[(decile == d) & (np.abs(dnet) > 1)])))} for d in range(1, 11)}
            out[version] = res; print(version, json.dumps(res), flush=True); del sim
    finally:
        release_lock()
    OUT.write_text(json.dumps(out, indent=2) + "\n"); print("done")

if __name__ == "__main__":
    main()
