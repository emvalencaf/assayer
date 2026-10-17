from dataclasses import dataclass, field


@dataclass
class Comparison:
    """The difference between two Experiments, always the second minus the first.

    Args:
        metric_deltas: Difference of the mean Score per (metric name, Field).
            None when the pair is scored on one side only.
        input_tokens_delta: Difference of the mean input tokens per Case.
        output_tokens_delta: Difference of the mean output tokens per Case.
        cost_usd_delta: Difference of the mean cost per Case. None without pricing.
            The token and cost deltas are None when either side has no recorded usage.
        only_in_a: Ids of the Cases that only the first Experiment has.
        only_in_b: Ids of the Cases that only the second Experiment has. The token
            and cost deltas leave out the Cases of both lists, so they compare like
            with like; the metric deltas do not.
    """

    metric_deltas: dict[tuple[str, str | None], float | None] = field(default_factory=dict)
    input_tokens_delta: float | None = None
    output_tokens_delta: float | None = None
    cost_usd_delta: float | None = None
    only_in_a: list[str | None] = field(default_factory=list)
    only_in_b: list[str | None] = field(default_factory=list)
