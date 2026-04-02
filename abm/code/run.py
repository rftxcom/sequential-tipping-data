"""Main entry point for running the Sequential Tipping Model experiments."""

import argparse
import os
import sys
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sequential_tipping_model.config import ModelConfig, ExperimentConfig
from sequential_tipping_model.experiments import (
    run_validation, run_experiment_1, run_experiment_2,
    run_experiment_3, run_experiment_4,
)
from sequential_tipping_model.analysis import (
    plot_validation, plot_experiment_1, plot_experiment_2,
    plot_experiment_3, plot_experiment_4, generate_summary_table,
)


def main():
    parser = argparse.ArgumentParser(
        description="Sequential Tipping Agent-Based Model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m sequential_tipping_model.run --validate
  python -m sequential_tipping_model.run --experiment 1
  python -m sequential_tipping_model.run --experiment all
  python -m sequential_tipping_model.run --experiment all --reps 50 --quick
        """,
    )
    parser.add_argument("--validate", action="store_true",
                        help="Run single-pillar validation against Xie et al.")
    parser.add_argument("--experiment", type=str, default=None,
                        help="Experiment to run: 1, 2, 3, 4, or 'all'")
    parser.add_argument("--reps", type=int, default=100,
                        help="Number of replications per parameter combo (default: 100)")
    parser.add_argument("--workers", type=int, default=None,
                        help="Number of parallel workers (default: all CPUs)")
    parser.add_argument("--results-dir", type=str, default=None,
                        help="Directory for output (default: results/ in model dir)")
    parser.add_argument("--quick", action="store_true",
                        help="Quick mode: fewer C values and replications for testing")
    parser.add_argument("--plot-only", action="store_true",
                        help="Only generate plots from existing CSV data")
    parser.add_argument("--summary", action="store_true",
                        help="Generate summary table from existing results")

    args = parser.parse_args()

    # Set results directory
    if args.results_dir:
        results_dir = args.results_dir
    else:
        results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
    os.makedirs(results_dir, exist_ok=True)

    model_config = ModelConfig.default()

    if args.quick:
        exp_config = ExperimentConfig(
            n_replications=min(args.reps, 20),
            c_min=0.02,
            c_max=0.30,
            c_steps=15,
            n_workers=args.workers,
        )
    else:
        exp_config = ExperimentConfig(
            n_replications=args.reps,
            n_workers=args.workers,
        )

    if args.summary:
        generate_summary_table(results_dir)
        return

    if args.plot_only:
        print("Generating plots from existing data...")
        _plot_all(results_dir, args.experiment)
        return

    if args.validate:
        t0 = time.time()
        run_validation(results_dir)
        plot_validation(results_dir)
        print(f"Validation completed in {time.time() - t0:.1f}s")

    if args.experiment:
        experiments = []
        if args.experiment == "all":
            experiments = [1, 2, 3, 4]
        else:
            experiments = [int(args.experiment)]

        for exp_num in experiments:
            t0 = time.time()
            print(f"\n{'='*60}")
            print(f"EXPERIMENT {exp_num}")
            print(f"{'='*60}")

            if exp_num == 1:
                run_experiment_1(exp_config, model_config, results_dir)
                plot_experiment_1(results_dir)
            elif exp_num == 2:
                run_experiment_2(exp_config, model_config, results_dir)
                plot_experiment_2(results_dir)
            elif exp_num == 3:
                run_experiment_3(exp_config, model_config, results_dir)
                plot_experiment_3(results_dir)
            elif exp_num == 4:
                run_experiment_4(exp_config, model_config, results_dir)
                plot_experiment_4(results_dir)

            elapsed = time.time() - t0
            print(f"Experiment {exp_num} completed in {elapsed:.1f}s")

        generate_summary_table(results_dir)

    if not args.validate and not args.experiment:
        parser.print_help()


def _plot_all(results_dir, experiment=None):
    """Generate all available plots."""
    plotters = {
        "validation": plot_validation,
        "1": plot_experiment_1,
        "2": plot_experiment_2,
        "3": plot_experiment_3,
        "4": plot_experiment_4,
    }

    if experiment and experiment != "all":
        plotters = {experiment: plotters.get(experiment)}

    for name, plotter in plotters.items():
        if plotter is None:
            continue
        try:
            plotter(results_dir)
            print(f"  Plotted {name}")
        except FileNotFoundError:
            print(f"  Skipped {name} (no data)")


if __name__ == "__main__":
    main()
