import argparse
from typing import Optional
from src.storage.experiment import ExperimentStorage
from src.api.serializers import UnifiedSerializer
from src.evaluation.metrics import MetricsCalculator
from src.models.experiment import AlgorithmRun
from src.models.types import FeatureType, RANSACType


def recompute(experiment_id: str, algorithm_key: Optional[str] = None):
    storage = ExperimentStorage()

    # Gather algorithms
    if algorithm_key:
        algorithms = [algorithm_key]
    else:
        exp = storage.get_experiment(experiment_id)
        if not exp:
            raise RuntimeError(f"Experiment not found: {experiment_id}")
        algorithms = list(exp.algorithms_tested)

    calc = MetricsCalculator()

    for alg in algorithms:
        # load frames
        frame_results, total = storage.get_frame_results(experiment_id, alg, 0, 1000000)
        if not frame_results:
            print(f"No frames for {alg}")
            continue

        # construct a minimal AlgorithmRun (types inferred from stored result)
        result = storage.get_algorithm_result(experiment_id, alg)
        if result is None:
            print(f"No stored metrics for {alg}, skip.")
            continue
        run = AlgorithmRun(
            experiment_id=experiment_id,
            algorithm_key=alg,
            feature_type=FeatureType(result.feature_type),
            ransac_type=RANSACType(result.ransac_type),
            sequence=alg.split("_")[-1],
            run_number=0,
        )

        # recompute with batch path (v1.1 semantics)
        new_metrics = calc.calculate_algorithm_metrics(run, frame_results)

        # persist
        storage.save_algorithm_result(experiment_id, alg, new_metrics)
        print(f"Recomputed metrics saved: {experiment_id}/{alg}")


def main():
    parser = argparse.ArgumentParser(description="Recompute AlgorithmMetrics for an experiment/algorithm (v1.1)")
    parser.add_argument("experiment_id", help="Experiment ID")
    parser.add_argument("--algorithm", help="Algorithm key (optional)")
    args = parser.parse_args()
    recompute(args.experiment_id, args.algorithm)


if __name__ == "__main__":
    main()

