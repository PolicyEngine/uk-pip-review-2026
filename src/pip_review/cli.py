"""Command line: ``pip-review generate``, ``household`` and ``reconcile``."""

import argparse
import json
from pathlib import Path

from pip_review import pipeline, publication
from pip_review.household import PRESETS_BY_ID, calculate
from pip_review.reforms import get_reform


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pip-review")
    commands = parser.add_subparsers(dest="command", required=True)

    generate = commands.add_parser("generate", help="Write data/results.json")
    generate.add_argument(
        "--mode", choices=["placeholder", "model"], default="placeholder"
    )
    generate.add_argument(
        "--status",
        choices=publication.STATUSES,
        help="Page status: placeholder (default in placeholder mode), mock on a "
        "drill branch, provisional (default in model mode) until G4, final",
    )
    generate.add_argument(
        "--banner", help="Banner text; defaults to the status's standard text"
    )
    generate.add_argument(
        "--dataset",
        help="Model mode: a dataset file instead of the bundle's certified "
        "national file (tests only; figures are never certified)",
    )
    generate.add_argument(
        "--measures", help="Model mode: comma-separated ids (default: all computable)"
    )
    generate.add_argument(
        "--no-households",
        action="store_true",
        help="Model mode: leave the example households out (faster)",
    )
    generate.add_argument(
        "--out", type=Path, default=pipeline.REPO_ROOT / "data" / "results.json"
    )
    generate.add_argument(
        "--dashboard-copy",
        type=Path,
        default=pipeline.REPO_ROOT / "dashboard" / "public" / "data" / "results.json",
    )

    household = commands.add_parser(
        "household", help="One preset household (needs the model extra)"
    )
    household.add_argument("preset", choices=sorted(PRESETS_BY_ID))
    household.add_argument("--reform")
    household.add_argument("--year", type=int)

    reconcile = commands.add_parser(
        "reconcile", help="Compare results.json with official costings (G3)"
    )
    reconcile.add_argument(
        "--results", type=Path, default=pipeline.REPO_ROOT / "data" / "results.json"
    )
    reconcile.add_argument(
        "--official",
        type=Path,
        nargs="*",
        help="Official costing CSVs (default: data_inputs/official/costings_*.csv)",
    )
    reconcile.add_argument("--reasons", type=Path, help="CSV of gap reasons")
    reconcile.add_argument("--out", type=Path, required=True)

    args = parser.parse_args(argv)
    if args.command == "generate":
        if args.mode == "placeholder":
            results = pipeline.build_placeholder_results(
                status=args.status or "placeholder", banner=args.banner
            )
        else:
            results = pipeline.build_model_results(
                dataset=args.dataset,
                status=args.status or "provisional",
                banner=args.banner,
                measure_ids=args.measures.split(",") if args.measures else None,
                households=not args.no_households,
            )
        pipeline.write_results(results, args.out, args.dashboard_copy)
        print(f"Wrote {args.out} and {args.dashboard_copy}")
        return 0
    if args.command == "reconcile":
        from pip_review import reconcile as rec

        rows, problems = rec.run(args.results, args.official, args.reasons, args.out)
        print(f"Wrote {args.out}: {len(rows)} rows, {len(problems)} problems")
        for problem in problems:
            print(problem)
        return 1 if problems else 0
    reform = get_reform(args.reform) if args.reform else None
    kwargs = {"year": args.year} if args.year else {}
    print(json.dumps(calculate(args.preset, reform, **kwargs), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
