"""Tests for the agent metrics."""

import pytest

from assayer.metrics import register_agent_metrics
from assayer.models import Case, Step, Trajectory
from assayer.registries import Registry


def _evaluate(registry, name, trajectory, case):
    return registry.get(name).evaluate(trajectory, case)


class TestStepEfficiency:
    @pytest.mark.parametrize(
        ("kinds", "expected", "value"),
        [
            (["model", "tool"], 4, 1.0),  # fewer steps than expected is capped at 1
            (["model", "tool", "tool", "model"], 4, 1.0),
            (["model", "tool", "tool", "model", "tool", "tool", "model", "model"], 4, 0.5),
            (["model", "retrieval", "other", "tool"], 1, 0.5),  # only model and tool count
            ([], 2, 0.0),  # no steps taken: no answer
            ([], 0, 1.0),
        ],
    )
    def test_documented_formula(self, kinds, expected, value):
        case = Case(input="q", id="c1", expected_steps=["s"] * expected)
        trajectory = Trajectory(steps=[Step(kind=k) for k in kinds], case_id="c1")
        registry = Registry()
        register_agent_metrics(registry)

        outcome = _evaluate(registry, "step_efficiency", trajectory, case)

        assert [(s.name, s.value) for s in outcome.scores] == [("step_efficiency", value)]

    def test_missing_expected_steps_is_a_failure_not_zero(self):
        registry = Registry()
        register_agent_metrics(registry)

        outcome = _evaluate(
            registry, "step_efficiency", Trajectory(steps=[Step(kind="model")]), Case(input="q")
        )

        assert outcome.scores == []
        assert outcome.failures[0].metric == "step_efficiency"

    def test_raw_measurements_never_become_scores(self):
        registry = Registry()
        register_agent_metrics(registry)
        case = Case(input="q", expected_steps=["s"])
        trajectory = Trajectory(steps=[Step(kind="model"), Step(kind="tool")])

        outcome = _evaluate(registry, "step_efficiency", trajectory, case)

        assert {s.name for s in outcome.scores} == {"step_efficiency"}


def _metric(name):
    registry = Registry()
    register_agent_metrics(registry)
    return registry.get(name)


def _tools(*names):
    return Trajectory(
        steps=[Step(kind="tool", id=f"s{i}", name=n) for i, n in enumerate(names)], case_id="c1"
    )


class TestToolCorrectness:
    @pytest.mark.parametrize(
        ("called", "expected", "value"),
        [
            (["a", "b"], ["a", "b"], 1.0),
            (["b", "a"], ["a", "b"], 1.0),  # unordered by default
            (["a"], ["a", "b"], pytest.approx(2 / 3)),  # missing tool
            (["a", "b", "c"], ["a", "b"], pytest.approx(0.8)),  # extra tool
            (["a", "a"], ["a"], pytest.approx(2 / 3)),  # multiset: repeats must be expected
            (["x"], ["a"], 0.0),
            ([], ["a"], 0.0),
            (["a"], [], 0.0),
            ([], [], 1.0),
        ],
    )
    def test_f1_over_the_multiset_of_names(self, called, expected, value):
        case = Case(input="q", expected_tool_calls=[{"name": n} for n in expected])

        outcome = _metric("tool_correctness").evaluate(_tools(*called), case)

        assert outcome.scores[0].value == value

    def test_expected_calls_may_be_plain_names(self):
        case = Case(input="q", expected_tool_calls=["a"])

        assert _metric("tool_correctness").evaluate(_tools("a"), case).scores[0].value == 1.0

    def test_non_tool_steps_are_ignored(self):
        trajectory = Trajectory(steps=[Step(kind="model", name="a"), Step(kind="tool", name="a")])
        case = Case(input="q", expected_tool_calls=["a"])

        assert _metric("tool_correctness").evaluate(trajectory, case).scores[0].value == 1.0

    def test_ordered_counts_only_the_expected_order(self):
        metric = _metric("tool_correctness")
        case = Case(input="q", expected_tool_calls=["a", "b", "c"])

        in_order = metric.evaluate(_tools("a", "b", "c"), case, params={"ordered": True})
        swapped = metric.evaluate(_tools("c", "b", "a"), case, params={"ordered": True})

        assert in_order.scores[0].value == 1.0
        assert swapped.scores[0].value == pytest.approx(1 / 3)

    def test_missing_expected_tool_calls_is_a_failure(self):
        outcome = _metric("tool_correctness").evaluate(_tools("a"), Case(input="q"))

        assert outcome.scores == []
        assert "expected_tool_calls" in outcome.failures[0].error


class TestToolArgumentMatch:
    @staticmethod
    def _trajectory(*calls):
        return Trajectory(
            steps=[
                Step(kind="tool", id=f"s{i}", name=name, input=args)
                for i, (name, args) in enumerate(calls)
            ],
            case_id="c1",
        )

    def test_mean_over_matched_calls_with_a_score_per_step(self):
        case = Case(
            input="q",
            expected_tool_calls=[
                {"name": "search", "arguments": {"q": "cats", "limit": 5}},
                {"name": "open", "arguments": {"id": 1}},
            ],
        )
        trajectory = self._trajectory(
            ("search", {"q": "cats", "limit": 10}), ("open", {"id": 1, "extra": True})
        )

        outcome = _metric("tool_argument_match").evaluate(trajectory, case)

        assert [(s.target, s.target_id, s.value) for s in outcome.scores] == [
            ("trajectory", "c1", 0.75),
            ("step", "s0", 0.5),
            ("step", "s1", 1.0),
        ]

    def test_calls_are_paired_by_name_not_position(self):
        case = Case(
            input="q",
            expected_tool_calls=[
                {"name": "a", "arguments": {"x": 1}},
                {"name": "b", "arguments": {"y": 2}},
            ],
        )

        outcome = _metric("tool_argument_match").evaluate(
            self._trajectory(("b", {"y": 2}), ("a", {"x": 1})), case
        )

        assert outcome.scores[0].value == 1.0

    def test_nested_arguments_are_compared_per_leaf(self):
        case = Case(
            input="q",
            expected_tool_calls=[{"name": "a", "arguments": {"f": {"k": 1, "j": 2}}}],
        )

        outcome = _metric("tool_argument_match").evaluate(
            self._trajectory(("a", {"f": {"k": 1, "j": 3}})), case
        )

        assert outcome.scores[0].value == 0.5

    def test_call_without_expected_arguments_scores_one(self):
        case = Case(input="q", expected_tool_calls=["a"])

        outcome = _metric("tool_argument_match").evaluate(self._trajectory(("a", {"z": 1})), case)

        assert outcome.scores[0].value == 1.0

    def test_no_matched_call_scores_zero_when_calls_were_expected(self):
        case = Case(input="q", expected_tool_calls=[{"name": "a", "arguments": {"x": 1}}])

        outcome = _metric("tool_argument_match").evaluate(self._trajectory(("b", {"x": 1})), case)

        assert [s.value for s in outcome.scores] == [0.0]

    def test_no_expected_calls_scores_one(self):
        outcome = _metric("tool_argument_match").evaluate(
            self._trajectory(), Case(input="q", expected_tool_calls=[])
        )

        assert outcome.scores[0].value == 1.0

    def test_missing_expected_tool_calls_is_a_failure(self):
        outcome = _metric("tool_argument_match").evaluate(self._trajectory(), Case(input="q"))

        assert outcome.scores == []
        assert outcome.failures


class TestEndStateMatch:
    @staticmethod
    def _evaluate(final_state, expected_state, **params):
        trajectory = Trajectory(final_state=final_state, case_id="c1")
        case = Case(input="q", expected_state=expected_state)
        return _metric("end_state_match").evaluate(trajectory, case, params=params)

    def test_scores_per_leaf_at_dotted_paths_plus_a_trajectory_mean(self):
        outcome = self._evaluate(
            {"order": {"status": "cancelled", "refund": 0}},
            {"order": {"status": "cancelled", "refund": 10}},
        )

        assert [(s.field, s.target, s.value) for s in outcome.scores] == [
            (None, "trajectory", 0.5),
            ("order.status", "trajectory", 1.0),
            ("order.refund", "trajectory", 0.0),
        ]

    def test_silently_failed_action_scores_below_one(self):
        # cancel_order(123) was called, yet the order is still active
        outcome = self._evaluate({"order": {"123": "active"}}, {"order": {"123": "cancelled"}})

        assert outcome.scores[0].value < 1.0

    def test_a_missing_leaf_scores_zero(self):
        outcome = self._evaluate({"a": 1}, {"a": 1, "b": 2})

        assert [(s.field, s.value) for s in outcome.scores] == [(None, 0.5), ("a", 1.0), ("b", 0.0)]

    def test_expected_state_is_a_subset_by_default(self):
        outcome = self._evaluate({"a": 1, "extra": 9}, {"a": 1})

        assert outcome.scores[0].value == 1.0

    def test_strict_penalises_extra_paths(self):
        outcome = self._evaluate({"a": 1, "extra": 9}, {"a": 1}, strict=True)

        assert [(s.field, s.value) for s in outcome.scores] == [
            (None, 0.5),
            ("a", 1.0),
            ("extra", 0.0),
        ]

    def test_lists_are_compared_by_index(self):
        outcome = self._evaluate({"items": ["x", "y"]}, {"items": ["x", "z"]})

        assert [(s.field, s.value) for s in outcome.scores][1:] == [
            ("items.0", 1.0),
            ("items.1", 0.0),
        ]

    def test_emptied_container_is_not_equal_to_a_full_one(self):
        outcome = self._evaluate({"items": []}, {"items": ["x"]})

        assert outcome.scores[0].value == 0.0

    def test_scalar_state_has_only_the_mean(self):
        outcome = self._evaluate("done", "done")

        assert [(s.field, s.value) for s in outcome.scores] == [(None, 1.0)]

    def test_expected_state_without_final_state_is_an_evaluation_failure(self):
        outcome = self._evaluate(None, {"a": 1})

        assert outcome.scores == []
        assert "final_state" in outcome.failures[0].error

    def test_case_without_expected_state_is_skipped(self):
        outcome = self._evaluate({"a": 1}, None)

        assert (outcome.scores, outcome.failures) == ([], [])


class TestEndStateMatchEmptyState:
    def test_empty_expected_state_is_a_subset_of_anything(self):
        trajectory = Trajectory(final_state={"a": 1}, case_id="c1")
        case = Case(input="q", expected_state={})

        outcome = _metric("end_state_match").evaluate(trajectory, case)

        assert [(s.field, s.value) for s in outcome.scores] == [(None, 1.0)]
