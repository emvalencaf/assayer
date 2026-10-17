"""Tests for the criteria judge, through the Runner with a fake Judge."""

import pytest

from assayer.judges import JudgeResponse, Prompt
from assayer.metrics import make_criteria_judge
from assayer.models import Case, Dataset, Step, TokenUsage, Trajectory
from assayer.runner import Runner


class FakeJudge:
    """Replies with the queued texts in order and records every call."""

    def __init__(self, *texts, usage=None):
        self.texts = list(texts)
        self.usage = usage
        self.calls = []

    def complete(self, messages, schema=None):
        self.calls.append((messages, schema))
        return JudgeResponse(text=self.texts.pop(0), usage=self.usage)


def _run(metric, judge_replies=None):
    dataset = Dataset("d", [Case(input="2+2?", id="c1")])
    return Runner(lambda q: "4", [metric]).run(dataset)


class TestScoring:
    def test_integer_score_is_normalised_to_unit_range(self):
        judge = FakeJudge('{"score": 4, "reason": "mostly right"}')
        metric = make_criteria_judge(judge, name="helpful", criteria="Is it helpful?")

        experiment = _run(metric)

        (score,) = experiment.scores
        assert score.name == "helpful"
        assert score.value == 0.75  # (4 - 1) / (5 - 1)
        assert score.comment == "mostly right"
        assert score.target == "trajectory"
        assert score.target_id == "c1"
        assert experiment.failures == []

    def test_binary_scale_maps_to_zero_or_one(self):
        judge = FakeJudge('{"score": 1, "reason": "met"}')
        metric = make_criteria_judge(judge, criteria="Goal met?", scale=(0, 1))

        (score,) = _run(metric).scores

        assert score.value == 1.0

    def test_step_level_judges_the_step_input_and_output(self):
        judge = FakeJudge('{"score": 5, "reason": "ok"}', '{"score": 1, "reason": "bad"}')
        metric = make_criteria_judge(judge, criteria="Good?", level="step")
        target = lambda q: Trajectory(
            steps=[
                Step(kind="tool", name="a", input="in-a", output="out-a"),
                Step(kind="tool", name="b", input="in-b", output="out-b"),
            ],
            final_output="x",
        )

        experiment = Runner(target, [metric]).run(Dataset("d", [Case(input="q", id="c1")]))

        assert [(s.target, s.value) for s in experiment.scores] == [("step", 1.0), ("step", 0.0)]
        first_user = judge.calls[0][0][1]["content"]
        assert "in-a" in first_user and "out-a" in first_user


class TestParsing:
    @pytest.mark.parametrize(
        "reply",
        [
            '```json\n{"score": 3, "reason": "fine"}\n```',
            '```\n{"score": 3, "reason": "fine"}\n```',
            'Here you go: {"score": 3, "reason": "fine"} Thanks.',
            '{"score": 3.0, "reason": "fine"}',
        ],
    )
    def test_tolerates_fences_and_surrounding_text(self, reply):
        metric = make_criteria_judge(FakeJudge(reply), criteria="c")

        experiment = _run(metric)

        assert [s.value for s in experiment.scores] == [0.5]

    def test_invalid_json_is_retried_once_then_succeeds(self):
        judge = FakeJudge("not json", '{"score": 5, "reason": "ok"}')
        metric = make_criteria_judge(judge, criteria="c")

        experiment = _run(metric)

        assert [s.value for s in experiment.scores] == [1.0]
        assert experiment.failures == []
        assert len(judge.calls) == 2

    @pytest.mark.parametrize(
        "reply",
        [
            "not json",
            '{"score": 9, "reason": "out of range"}',
            '{"score": 3}',
            '{"score": 3, "reason": "  "}',
            '{"score": "three", "reason": "x"}',
            '{"score": true, "reason": "x"}',
            '{"score": 2.5, "reason": "x"}',
            "[1, 2]",
        ],
    )
    def test_two_invalid_replies_are_a_failure_never_a_zero(self, reply):
        judge = FakeJudge(reply, reply)
        metric = make_criteria_judge(judge, name="quality", criteria="c")

        experiment = _run(metric)

        assert experiment.scores == []
        (failure,) = experiment.failures
        assert failure.metric == "quality"
        assert failure.target_id == "c1"
        assert len(judge.calls) == 2

    def test_a_judge_that_raises_is_a_failure(self):
        class Broken:
            def complete(self, messages, schema=None):
                raise RuntimeError("rate limited")

        experiment = _run(make_criteria_judge(Broken(), criteria="c"))

        assert experiment.scores == []
        assert "rate limited" in experiment.failures[0].error


class TestAccounting:
    def test_judge_calls_and_tokens_are_kept_apart_from_the_target(self):
        usage = TokenUsage(input_tokens=10, output_tokens=2, cost_usd=None)
        judge = FakeJudge("bad", '{"score": 5, "reason": "ok"}', usage=usage)
        metric = make_criteria_judge(judge, criteria="c")
        target = lambda q: Trajectory(
            steps=[Step(kind="model", usage=TokenUsage(7, 3, None))], final_output="4"
        )

        experiment = Runner(target, [metric]).run(Dataset("d", [Case(input="q", id="c1")]))

        assert experiment.judge_calls == 2  # the retry counts
        assert experiment.judge_usage == TokenUsage(20, 4, None)
        assert experiment.total_usage() == TokenUsage(7, 3, None)

    def test_failed_attempts_still_cost(self):
        usage = TokenUsage(input_tokens=5, output_tokens=1, cost_usd=None)
        judge = FakeJudge("x", "y", usage=usage)

        experiment = _run(make_criteria_judge(judge, criteria="c"))

        assert experiment.failures
        assert experiment.judge_calls == 2
        assert experiment.judge_usage == TokenUsage(10, 2, None)

    def test_calls_without_reported_usage_leave_tokens_unknown(self):
        judge = FakeJudge('{"score": 5, "reason": "ok"}')

        experiment = _run(make_criteria_judge(judge, criteria="c"))

        assert experiment.judge_calls == 1
        assert experiment.judge_usage is None


class TestPrompts:
    def test_criteria_steps_and_rubric_reach_the_judge(self):
        judge = FakeJudge('{"score": 4, "reason": "ok"}')
        metric = make_criteria_judge(
            judge,
            criteria="Is it polite?",
            evaluation_steps=["Read the answer", "Look for rudeness"],
            rubric={1: "rude", 5: "courteous"},
        )

        _run(metric)

        system, user = judge.calls[0][0]
        assert system["role"] == "system" and user["role"] == "user"
        text = user["content"]
        for expected in (
            "Is it polite?",
            "1. Read the answer",
            "2. Look for rudeness",
            "1: rude",
            "5: courteous",
            "2+2?",
            "4",
        ):
            assert expected in text
        assert "1 to 5" in user["content"] or "from 1 to 5" in system["content"]

    def test_the_response_schema_is_passed_to_the_judge(self):
        judge = FakeJudge('{"score": 4, "reason": "ok"}')

        _run(make_criteria_judge(judge, criteria="c"))

        schema = judge.calls[0][1]
        assert schema["required"] == ["score", "reason"]
        assert schema["properties"]["score"]["maximum"] == 5

    def test_score_records_prompt_id_version_and_hash(self):
        judge = FakeJudge('{"score": 4, "reason": "ok"}')

        (score,) = _run(make_criteria_judge(judge, criteria="c")).scores

        assert score.metadata["prompt"] == "criteria@1"
        assert len(score.metadata["prompt_hash"]) == 64

    def test_default_prompt_can_be_replaced(self):
        prompt = Prompt(
            id="mine",
            version="3",
            system="Judge $low-$high, JSON only.",
            user="Q: $input\nA: $output",
        )
        judge = FakeJudge('{"score": 2, "reason": "meh"}')
        dataset = Dataset("d", [Case(input="q", id="c1")])

        experiment = Runner(
            lambda q: "a", [make_criteria_judge(judge, criteria="c", prompt=prompt)]
        ).run(dataset)

        assert judge.calls[0][0][1]["content"] == "Q: q\nA: a"
        (score,) = experiment.scores
        assert score.metadata["prompt"] == "mine@3"

    def test_changing_the_text_changes_the_hash(self):
        a = Prompt("p", "1", "sys", "user")
        b = Prompt("p", "1", "sys", "user!")

        assert a.hash != b.hash and a.ref == b.ref


class TestConstruction:
    def test_needs_criteria_or_steps(self):
        with pytest.raises(ValueError, match="criteria"):
            make_criteria_judge(FakeJudge(), criteria=" ")

    def test_rejects_unknown_prompt_placeholder(self):
        with pytest.raises(ValueError, match="nope"):
            make_criteria_judge(
                FakeJudge(), criteria="c", prompt=Prompt("p", "1", "$nope", "$input")
            )

    def test_rubric_must_sit_inside_the_scale(self):
        with pytest.raises(ValueError, match="rubric"):
            make_criteria_judge(FakeJudge(), criteria="c", rubric={9: "x"})

    def test_missing_output_is_a_failure_not_a_zero(self):
        judge = FakeJudge()
        dataset = Dataset("d", [Case(input="q", id="c1")])

        experiment = Runner(lambda q: None, [make_criteria_judge(judge, criteria="c")]).run(dataset)

        assert experiment.scores == []
        assert "final_output" in experiment.failures[0].error
        assert judge.calls == []
