from assayer.adapters import InMemoryAdapter, score_ids, trajectory_id
from assayer.metrics.metric import Metric
from assayer.models import Case, Dataset
from assayer.runner import Runner


def test_trajectory_id_is_stable_and_distinguishes_repetitions():
    assert trajectory_id("e", "c1", 0) == trajectory_id("e", "c1", 0)
    assert trajectory_id("e", "c1", 0) != trajectory_id("e", "c1", 1)
    assert trajectory_id("e", "c1", 0) != trajectory_id("other", "c1", 0)


def test_scores_of_the_same_metric_on_repetitions_get_distinct_ids():
    metric = Metric(name="m", level="trajectory", fn=lambda t, c: 1.0)
    experiment = Runner(lambda v: v, [metric], repetitions=3).run(
        Dataset("d", [Case(input="a", id="c1")])
    )

    ids = score_ids(experiment)

    assert len(set(ids)) == 3
    assert ids == score_ids(experiment)


def test_trajectory_scores_attach_to_the_repetition_they_came_from():
    metric = Metric(name="m", level="trajectory", fn=lambda t, c: 1.0)
    runner = Runner(lambda v: v, [metric], repetitions=2, adapter=InMemoryAdapter())
    experiment = runner.run(Dataset("d", [Case(input="a", id="c1")]))
    runner.export(experiment)

    scores = [p for i, p in runner.adapter.items.items() if i.target_kind == "score"]
    trajectories = {
        p["id"]: p["repetition"]
        for i, p in runner.adapter.items.items()
        if i.target_kind == "trajectory"
    }

    assert sorted(trajectories[s["target_id"]] for s in scores) == [0, 1]
