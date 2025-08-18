from src.api.services.result import ResultService
from src.models.evaluation import AlgorithmMetrics


def test_success_rate_from_metrics(monkeypatch):
    rs = ResultService()

    class DummyExp:
        class Cfg:
            pass
        config = Cfg()

    # Stub storage get_experiment and get_algorithm_result
    def fake_get_experiment(exp_id):
        return DummyExp()

    class M:
        algorithm_key = "ALG1"
        success_rate = 0.42

        class Metrics:
            success_rate = 0.42

        metrics = Metrics()

    def fake_get_alg(exp_id, alg):
        return M()

    monkeypatch.setattr(rs.experiment_storage, "get_experiment", fake_get_experiment)
    monkeypatch.setattr(rs.experiment_storage, "get_algorithm_result", fake_get_alg)

    # call a method that constructs trajectory where success_rate is used
    # We call private builder indirectly via get_trajectory_data by stubbing frame results
    def fake_get_frame_results(exp_id, alg, start, limit):
        # Return some dummy frame results to trigger trajectory building
        class MockFrame:
            def __init__(self):
                self.timestamp = 0.1
                self.estimated_pose = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
        return [MockFrame()], 1

    monkeypatch.setattr(rs.experiment_storage, "get_frame_results", fake_get_frame_results)

    data = rs.get_trajectory_data("exp1", "ALG1")
    assert data["statistics"]["success_rate"] == 0.42

