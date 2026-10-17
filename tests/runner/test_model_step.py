"""Tests for model_step."""

from types import SimpleNamespace

from assayer.models import Case, Dataset, PricingConfig, Trajectory
from assayer.runner import Runner, model_step


def _reply(**kwargs):
    return SimpleNamespace(content="4", **kwargs)


def test_content_and_usage_become_a_model_step():
    step = model_step(
        _reply(usage_metadata={"input_tokens": 3, "output_tokens": 2}),
        model="m",
        input="2 + 2?",
    )

    assert (step.kind, step.model, step.input, step.output) == ("model", "m", "2 + 2?", "4")
    assert (step.usage.input_tokens, step.usage.output_tokens, step.usage.cost_usd) == (3, 2, None)


def test_missing_counts_default_to_zero_and_string_counts_are_coerced():
    step = model_step(_reply(usage_metadata={"input_tokens": "5"}))

    assert (step.usage.input_tokens, step.usage.output_tokens) == (5, 0)


def test_a_reply_without_usage_metadata_has_no_usage_not_zero():
    assert model_step(_reply()).usage is None
    assert model_step(_reply(usage_metadata=None)).usage is None


def test_a_reply_without_content_is_kept_as_the_output():
    assert model_step("plain text").output == "plain text"


def test_the_runner_prices_the_step():
    pricing = PricingConfig(cost_per_input_token=1.0, cost_per_output_token=2.0)
    reply = _reply(usage_metadata={"input_tokens": 3, "output_tokens": 2})

    experiment = Runner(
        lambda q: Trajectory(steps=[model_step(reply)], final_output="4"), pricing=pricing
    ).run(Dataset("d", [Case(input="q", id="c1")]))

    usage = experiment.trajectories[0].total_usage(experiment.pricing)
    assert usage.cost_usd == 7.0
