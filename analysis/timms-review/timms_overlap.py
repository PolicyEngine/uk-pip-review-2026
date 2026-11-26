#!/usr/bin/env python3
"""Baseline overlap between the UC health (LCWRA) element and PIP daily living,
for the Timms Review post. Current law, certified bundle (policyengine 6.20.3,
build b891aa69). Counts people who are UC claimants whose award includes the
LCWRA element on their account (claimant with LCWRA, award has element), and
people receiving PIP daily living. Disclosure floor: 3 survey households per cell.
"""
import json, os, sys, time
from pathlib import Path
ROOT = Path(os.environ.get("MILBURN_DASHBOARD", "../uk-milburn-review-dashboard")).resolve()
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
from milburn_one_off_figures import release_lock, take_lock  # noqa: E402

YEARS = (2026, 2029)
OUT = Path(__file__).parent / "results" / "timms_overlap_raw.json"
FLOOR = 3

def main():
    import numpy as np
    for n in ("HUGGING_FACE_TOKEN", "HF_TOKEN", "HUGGINGFACE_HUB_TOKEN"):
        os.environ.pop(n, None)
    from uk_budget_data import local_build
    from uk_budget_data.models import DataConfig
    from uk_budget_data.pipeline import build_microsimulation, scatter_survey_households
    from uk_budget_data.reforms import get_reform
    from policyengine_core.periods import period as as_period
    from policyengine_uk.utils.uc_work_related_requirements import other_member_of_single_claim
    local_build.check_engine(); local_build.check_dataset()
    take_lock()
    out = {"build": local_build.LABEL, "years": {}}
    try:
        config = DataConfig()
        path = str(config.dataset_path) if config.dataset_path else None
        pkg = get_reform("milburn_report_package")
        sim = build_microsimulation(path, pkg.baseline_scenario_for(config))
        survey_hh = np.asarray(scatter_survey_households(sim, path))  # household-level survey id
        person = sim.populations["person"]
        for y in YEARS:
            per = as_period(y)
            a = lambda v, e=None: np.asarray(sim.calculate(v, y, map_to="person") if e else sim.calculate(v, y), dtype=float)
            w = a("person_weight")
            age = a("age")
            hh_id_p = np.asarray(sim.calculate("household_id", y, map_to="person"))
            hh_id_h = np.asarray(sim.calculate("household_id", y))
            sv = dict(zip(hh_id_h, survey_hh))
            svp = np.array([sv[h] for h in hh_id_p])
            claimant = np.asarray(person("is_uc_assessed_claimant", per) & ~other_member_of_single_claim(person, per))
            lcwra = np.asarray(person("uc_limited_capability_for_WRA", per))
            elem_bu = np.asarray(sim.calculate("uc_LCWRA_element", y, map_to="person"), dtype=float) > 0
            uc = np.asarray(sim.calculate("universal_credit", y, map_to="person"), dtype=float) > 0
            health = claimant & lcwra & elem_bu & uc
            pipdl = a("pip_dl") > 0
            groups = {"all": np.ones_like(age, bool), "16_24": (age >= 16) & (age <= 24), "25_64": (age >= 25) & (age <= 64)}
            res = {}
            for g, m in groups.items():
                cells = {
                    "health": health & m,
                    "health_and_pipdl": health & pipdl & m,
                    "health_no_pipdl": health & ~pipdl & m,
                    "uc_claimant_pipdl_no_health": claimant & uc & pipdl & ~health & m,
                }
                r = {}
                for k, mask in cells.items():
                    n = int(len(set(svp[mask])))
                    r[k] = {"people": float(np.sum(w[mask])) if n >= FLOOR else None, "survey_households": n}
                h = r["health"]["people"]; b = r["health_and_pipdl"]["people"]
                r["share_with_pipdl"] = (b / h) if h and b else None
                res[g] = r
            out["years"][y] = res
            print(y, json.dumps(res), flush=True)
    finally:
        release_lock()
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
