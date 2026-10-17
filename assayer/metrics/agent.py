"""Metrics over what an agent did, scored on its Trajectory."""

from collections import Counter
from collections.abc import Mapping
from typing import Any

from assayer.alignment import align_by_key
from assayer.metrics.metric import Detailed, Metric
from assayer.models import Case, Score, Step, Trajectory

_COUNTED_KINDS = ("model", "tool")


def step_efficiency(trajectory: Trajectory, case: Case) -> float:
    """Score how close the run stayed to the expected number of Steps.

    Computes `min(1, expected_steps / actual_steps)`, where `expected_steps` is
    the length of `Case.expected_steps` and `actual_steps` counts only the
    `model` and `tool` Steps of the Trajectory. A run that took no such Step
    scores 0 unless none was expected, which scores 1.

    Args:
        trajectory: The Trajectory to score.
        case: The Case holding the expected Steps.

    Returns:
        A value in [0, 1]; 1 means no more Steps than expected.
    """
    expected = len(case.expected_steps or [])
    actual = sum(step.kind in _COUNTED_KINDS for step in trajectory.steps)
    if actual == 0:
        return 1.0 if expected == 0 else 0.0
    return min(1.0, expected / actual)


def _call_name(call: Any) -> Any:
    """Name of an expected tool call: the call itself when a string, else its "name"."""
    return call.get("name") if isinstance(call, Mapping) else call


def _call_arguments(call: Any) -> Any:
    return call.get("arguments") if isinstance(call, Mapping) else None


def _tool_steps(trajectory: Trajectory) -> list[Step]:
    return [step for step in trajectory.steps if step.kind == "tool"]


def _f1(matched: int, n_predicted: int, n_expected: int) -> float:
    if not n_predicted and not n_expected:
        return 1.0
    if not matched:
        return 0.0
    precision, recall = matched / n_predicted, matched / n_expected
    return 2 * precision * recall / (precision + recall)


def _longest_common_subsequence(a: list, b: list) -> int:
    row = [0] * (len(b) + 1)
    for x in a:
        previous = 0
        for j, y in enumerate(b, start=1):
            previous, row[j] = row[j], previous + 1 if x == y else max(row[j], row[j - 1])
    return row[-1]


def tool_correctness(trajectory: Trajectory, case: Case, ordered: bool = False) -> float:
    """Score the tools called against the expected ones by F1 over their names.

    The names of the `tool` Steps are compared with those of `Case.expected_tool_calls`
    (each a name, or a dictionary with a "name") as multisets: a tool called twice must
    be expected twice. Arguments are left to `tool_argument_match`.

    Args:
        trajectory: The Trajectory whose tool Steps are scored.
        case: The Case holding the expected tool calls.
        ordered: Count only the names that appear in the expected order (the longest
            common subsequence) instead of every name present.

    Returns:
        A value in [0, 1]; two empty sequences score 1, tools called when none were
        expected (or the reverse) score 0.
    """
    called = [step.name for step in _tool_steps(trajectory)]
    expected = [_call_name(call) for call in case.expected_tool_calls or []]
    if ordered:
        matched = _longest_common_subsequence(expected, called)
    else:
        matched = sum((Counter(expected) & Counter(called)).values())
    return _f1(matched, len(called), len(expected))


def _leaves(value: Any, path: str = "") -> dict[str, Any]:
    """Flatten nested dictionaries and lists into `{dotted path: leaf}`.

    A nested empty container is a leaf, so that emptying it is not mistaken for nothing.
    """
    if isinstance(value, Mapping) and value:
        items = value.items()
    elif isinstance(value, (list, tuple)) and value:
        items = enumerate(value)
    elif path or not isinstance(value, (Mapping, list, tuple)):
        return {path: value}
    else:
        return {}  # an empty state as a whole has no leaves to expect
    leaves: dict[str, Any] = {}
    for key, child in items:
        leaves.update(_leaves(child, f"{path}.{key}" if path else str(key)))
    return leaves


def _compare_leaves(expected: Any, actual: Any, strict: bool = False) -> dict[str, float]:
    """Score each leaf by exact equality, pairing expected and actual leaves by path.

    Returns:
        1.0 or 0.0 per expected leaf (0 when absent), plus 0.0 per extra leaf when strict.
    """
    wanted, found = _leaves(expected), _leaves(actual)
    alignment = align_by_key(
        [{"path": p} for p in wanted], [{"path": p} for p in found], key="path"
    )
    paths_wanted, paths_found = list(wanted), list(found)
    scores = {
        paths_wanted[e]: float(wanted[paths_wanted[e]] == found[paths_found[p]])
        for e, p in alignment.pairs
    }
    scores.update({paths_wanted[e]: 0.0 for e in alignment.unmatched_expected})
    if strict:
        scores.update({paths_found[p]: 0.0 for p in alignment.unmatched_predicted})
    return scores


def _mean(values) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 1.0


def tool_argument_match(trajectory: Trajectory, case: Case) -> Detailed:
    """Score the arguments of the tools called against the expected ones.

    Each expected call is paired with the earliest unpaired `tool` Step of the same
    name. A pair scores the share of expected argument leaves (dotted paths, exact
    equality) that the Step's `input` holds with the same value; extra arguments are
    not penalised and a call that expects none scores 1. Expected calls with no Step
    are left to `tool_correctness`.

    Args:
        trajectory: The Trajectory whose tool Steps are scored.
        case: The Case holding the expected tool calls.

    Returns:
        The mean over the matched calls (0 when calls were expected and none matched, 1
        when none were expected), plus one Score per matched Step, targeting that Step.
    """
    expected = case.expected_tool_calls or []
    steps = _tool_steps(trajectory)
    alignment = align_by_key(
        [{"name": _call_name(call)} for call in expected],
        [{"name": step.name} for step in steps],
        key="name",
    )
    values, details = [], []
    for e, p in alignment.pairs:
        arguments = _call_arguments(expected[e])
        value = (
            1.0 if arguments is None else _mean(_compare_leaves(arguments, steps[p].input).values())
        )
        values.append(value)
        if steps[p].id is not None:
            details.append(
                Score(name="tool_argument_match", value=value, target="step", target_id=steps[p].id)
            )
    return Detailed(_mean(values) if values or not expected else 0.0, details)


def end_state_match(trajectory: Trajectory, case: Case, strict: bool = False) -> Detailed | None:
    """Score how much of the expected end state the run left behind.

    Compares `Trajectory.final_state` with `Case.expected_state` leaf by leaf (dotted
    paths, exact equality), whatever path the agent took: a tool that was called
    but changed nothing leaves its leaf wrong.

    Args:
        trajectory: Its `final_state` is the state observed after the run.
        case: Its `expected_state` is the state wanted.
        strict: Also penalise the leaves of `final_state` that are not expected, each
            scoring 0. By default the expected state is a subset.

    Returns:
        The mean over the leaves as the Trajectory's value, plus one Score per leaf at
        its dotted path; None (skipped) when the Case has no `expected_state`.

    Raises:
        ValueError: If the Case has an `expected_state` and the Trajectory no `final_state`.
    """
    if case.expected_state is None:
        return None
    if trajectory.final_state is None:
        raise ValueError("missing required input: final_state")
    leaves = _compare_leaves(case.expected_state, trajectory.final_state, strict)
    details = [
        Score(name="end_state_match", value=value, field=path, target_id=trajectory.case_id)
        for path, value in leaves.items()
        if path
    ]
    return Detailed(_mean(leaves.values()), details)


def register_agent_metrics(registry) -> None:
    """Register the agent metrics into a registry.

    Args:
        registry: The Registry to fill.
    """
    registry.register(
        Metric(
            name="step_efficiency",
            level="trajectory",
            requires=("expected_steps",),
            fn=step_efficiency,
        )
    )
    registry.register(
        Metric(
            name="tool_correctness",
            level="trajectory",
            requires=("expected_tool_calls",),
            fn=tool_correctness,
        )
    )
    registry.register(
        Metric(
            name="tool_argument_match",
            level="trajectory",
            requires=("expected_tool_calls",),
            fn=tool_argument_match,
        )
    )
    registry.register(Metric(name="end_state_match", level="trajectory", fn=end_state_match))
