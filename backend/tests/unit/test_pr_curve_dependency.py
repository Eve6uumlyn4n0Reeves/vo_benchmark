import pytest
from src.api.services.result import ResultService


def test_pr_curve_missing_dependency(monkeypatch):
    rs = ResultService()

    # Mock experiment storage to return a valid experiment
    class MockExperiment:
        pass

    def mock_get_experiment(exp_id):
        return MockExperiment()

    def mock_get_pr_curve(exp_id, alg_key):
        return None  # No precomputed data

    def mock_get_algorithm_result(exp_id, alg_key):
        class MockAlgorithmResult:
            pass
        return MockAlgorithmResult()

    def mock_get_frame_results(exp_id, alg_key, start, limit):
        # Return some dummy frame results to trigger computation
        class MockRansac:
            inlier_mask = [True, False, True]

        class MockMatches:
            scores = [0.8, 0.6, 0.9]

        class MockFrame:
            def __init__(self):
                self.matches = MockMatches()
                self.ransac = MockRansac()
                self.scores = [0.8, 0.6, 0.9]
                self.labels = [True, False, True]
        return [MockFrame()], 1

    # Simulate sklearn import failure in compute function
    def fake_compute(*args, **kwargs):
        raise RuntimeError("PR curve computation requires scikit-learn")

    monkeypatch.setattr(rs.experiment_storage, "get_experiment", mock_get_experiment)
    monkeypatch.setattr(rs.experiment_storage, "get_pr_curve", mock_get_pr_curve)
    monkeypatch.setattr(rs.experiment_storage, "get_algorithm_result", mock_get_algorithm_result)
    monkeypatch.setattr(rs.experiment_storage, "get_frame_results", mock_get_frame_results)
    monkeypatch.setattr(rs, "_compute_pr_curve_inline", fake_compute)

    with pytest.raises(RuntimeError, match="PR curve computation requires scikit-learn"):
        rs.get_pr_curve("exp_1", "ALG1")

