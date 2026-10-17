"""Conformance suite every Adapter must pass, run through the Runner's export path.

Subclass `AdapterConformance` and implement the three hooks; pytest collects the subclass.
"""

import pytest

from assayer.adapters import Adapter, AdapterCallError
from assayer.metrics.metric import Detailed, Metric
from assayer.models import Case, Dataset, Score, Step, Trajectory
from assayer.runner import Runner


def _exact(trajectory, case):
    return trajectory.final_output == case.expected_output


def _step_len(step, case):
    return 1.0


EXACT = Metric(name="exact", level="trajectory", fn=_exact, requires=("expected_output",))
PER_STEP = Metric(name="per_step", level="step", fn=_step_len)


def _target(value):
    return Trajectory(
        steps=[
            Step(kind="tool", id=None, name="search", input=value, output="secret-hit"),
            Step(kind="model", input=value, output=f"answer-{value}"),
        ],
        final_output=f"answer-{value}",
        final_state={"done": True},
    )


class AdapterConformance:
    """Behavior shared by all Adapters. Subclasses provide the hooks."""

    def make_adapter(self) -> Adapter:
        raise NotImplementedError

    def inject(self, adapter, target_kind, *errors, nth=0):
        """Make the `nth` item of a kind fail with `errors`, one per attempt."""
        raise NotImplementedError

    def stored(self, adapter) -> dict:
        """Everything the backend now holds: `{(target_kind, target_id): payload}`."""
        raise NotImplementedError

    @pytest.fixture
    def adapter(self):
        return self.make_adapter()

    @pytest.fixture
    def runner(self, adapter):
        return Runner(_target, [EXACT, PER_STEP], repetitions=2, adapter=adapter)

    @pytest.fixture
    def experiment(self, runner):
        dataset = Dataset(
            "d",
            [
                Case(input="a", id="c1", expected_output="answer-a"),
                Case(input="b", id="c2", expected_output="nope"),
            ],
        )
        return runner.run(dataset)

    def test_exports_everything_and_confirms_or_queues_it(self, runner, experiment, adapter):
        report = runner.export(experiment)

        assert report.ok
        assert not report.failed and not report.skipped
        delivered = {(i.target_kind, i.target_id) for i in [*report.confirmed, *report.queued]}
        assert delivered == set(self.stored(adapter))
        kinds = [i.target_kind for i in [*report.confirmed, *report.queued]]
        assert kinds.count("case") == 2
        assert kinds.count("trajectory") == 4
        assert kinds.count("step") == 8
        assert kinds.count("score") == len(experiment.scores) == 4 + 8

    def test_reexport_is_idempotent(self, runner, experiment, adapter):
        runner.export(experiment)
        first = {k: dict(v) for k, v in self.stored(adapter).items()}

        report = runner.export(experiment)

        assert report.ok
        assert self.stored(adapter) == first

    def test_same_experiment_gets_same_ids_in_a_new_adapter(self, runner, experiment):
        runner.export(experiment)
        other = self.make_adapter()
        Runner(adapter=other).export(experiment)

        assert set(self.stored(other)) == set(self.stored(runner.adapter))

    def test_partial_failure_is_reported_not_raised(self, runner, experiment, adapter):
        self.inject(adapter, "step", AdapterCallError("validation", "bad step"), nth=1)

        report = runner.export(experiment)

        assert not report.ok
        (failure,) = report.failed
        assert (failure.target_kind, failure.kind, failure.retryable) == (
            "step",
            "validation",
            False,
        )
        assert failure.message == "bad step"
        assert report.skipped == []
        assert ("step", failure.target_id) not in self.stored(adapter)
        assert len(report.confirmed) + len(report.queued) == 2 + 4 + 8 + 12 - 1

    def test_auth_failure_aborts_and_skips_the_rest(self, runner, experiment, adapter):
        self.inject(adapter, "trajectory", AdapterCallError("auth", "bad key"), nth=1)

        report = runner.export(experiment)

        assert not report.ok
        (failure,) = report.failed
        assert failure.kind == "auth"
        delivered = len(report.confirmed) + len(report.queued)
        assert delivered == 2 + 1 + 2  # both Cases, the first Trajectory and its Steps
        assert delivered + 1 + len(report.skipped) == 2 + 4 + 8 + 12
        assert ("trajectory", failure.target_id) not in {
            (i.target_kind, i.target_id) for i in report.skipped
        }
        assert all(item.target_kind in ("step", "trajectory", "score") for item in report.skipped)

    def test_transient_failure_is_retried(self, runner, experiment, adapter):
        transient = AdapterCallError("rate_limited", "slow down", retry_after=2)
        self.inject(adapter, "case", transient, transient)

        report = runner.export(experiment)

        assert report.ok

    def test_failure_that_outlasts_the_retries_is_reported_as_retryable(
        self, runner, experiment, adapter
    ):
        transient = AdapterCallError("transport", "reset")
        self.inject(adapter, "score", transient, transient, transient, nth=0)

        report = runner.export(experiment)

        (failure,) = report.failed
        assert (failure.kind, failure.retryable) == ("transport", True)

    def test_unexpected_exception_is_reported_as_unknown(self, runner, experiment, adapter):
        self.inject(adapter, "case", AdapterCallError("unknown", "huh"))

        (failure,) = runner.export(experiment).failed

        assert failure.kind == "unknown"

    def test_without_content_only_structure_scores_and_metadata_are_sent(
        self, runner, experiment, adapter
    ):
        report = runner.export(experiment, include_content=False)

        assert report.ok
        payloads = self.stored(adapter)
        assert "secret-hit" not in repr(payloads)
        assert "answer-a" not in repr([v for k, v in payloads.items() if k[0] != "score"])
        scores = [v for k, v in payloads.items() if k[0] == "score"]
        assert sorted(s["name"] for s in scores).count("exact") == 4
        assert {s["value"] for s in scores if s["name"] == "exact"} == {0.0, 1.0}
        steps = [v for k, v in payloads.items() if k[0] == "step"]
        assert {s["kind"] for s in steps} == {"tool", "model"}

    def test_with_content_final_output_and_state_are_sent(self, runner, experiment, adapter):
        runner.export(experiment)

        trajectories = [v for k, v in self.stored(adapter).items() if k[0] == "trajectory"]

        assert {t["final_output"] for t in trajectories} == {"answer-a", "answer-b"}
        assert all(t["final_state"] == {"done": True} for t in trajectories)
        assert sorted(t["repetition"] for t in trajectories) == [0, 0, 1, 1]

    def test_context_manager_closes(self):
        with self.make_adapter() as adapter:
            assert isinstance(adapter, Adapter)
            assert adapter.name

    def test_without_content_step_errors_and_score_comments_are_left_out(self, adapter):
        def target(value):
            return Trajectory(steps=[Step(kind="tool", error="Traceback: secret-input")])

        judged = Metric(
            name="judged",
            level="trajectory",
            fn=lambda t, c: Detailed(1.0, comment="quotes secret"),
        )
        runner = Runner(target, [judged], adapter=adapter)
        experiment = runner.run(Dataset("d", [Case(input="a", id="c1")]))

        report = runner.export(experiment, include_content=False)

        assert report.ok
        assert "secret" not in repr(self.stored(adapter))

    def test_scores_that_cannot_be_linked_are_noted_not_lost(self, adapter):
        runner = Runner(_target, adapter=adapter)
        experiment = runner.run(Dataset("d", [Case(input="a", id="c1")]))
        experiment.scores.append(Score("orphan", 1.0, target="step", target_id="nowhere"))

        report = runner.export(experiment)

        assert report.ok
        assert any("orphan" in note for note in report.notes)

    def test_an_experiment_that_cannot_be_planned_is_a_failure_not_an_exception(self, adapter):
        runner = Runner(_target, adapter=adapter)
        experiment = runner.run(Dataset("d", [Case(input="a", id="c1")]))
        experiment.trajectories = None

        (failure,) = runner.export(experiment).failed

        assert (failure.target_kind, failure.kind) == ("experiment", "validation")
