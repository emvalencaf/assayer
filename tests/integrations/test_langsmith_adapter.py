"""LangSmithAdapter, held to the shared conformance suite, plus what is its own.

The client is `create_autospec(langsmith.Client)` backed by a small in-memory `Backend`, so
every call is checked against the real signatures. `test_live_smoke` runs only with credentials.
"""

import datetime as dt
import os
import uuid
from collections import defaultdict, deque
from types import SimpleNamespace
from unittest.mock import create_autospec, patch

import langsmith
import pytest
from langsmith.utils import (
    LangSmithAuthError,
    LangSmithConflictError,
    LangSmithConnectionError,
    LangSmithRateLimitError,
)

from assayer.adapters import AdapterCallError, AdapterConfigError
from assayer.integrations.langsmith_adapter import LangSmithAdapter
from assayer.metrics.metric import Detailed, Metric
from assayer.models import Case, Dataset, PricingConfig, Score, Step, TokenUsage, Trajectory
from assayer.runner import Runner

from ..adapters.conformance import AdapterConformance

START = dt.datetime(2026, 10, 17, 12, 0, 0, tzinfo=dt.UTC)


class Backend:
    """What LangSmith would hold after the calls, keyed by the ids the adapter chose."""

    def __init__(self):
        self.datasets = {}
        self.projects = {}
        self.examples = {}
        self.runs = {}
        self.feedback = {}
        self._faults = defaultdict(dict)
        self._position = {}
        self._counts = defaultdict(int)

    def fail_on(self, kind, errors, nth):
        self._faults[kind][nth] = deque(errors)

    def check(self, kind, item_id):
        if (kind, item_id) not in self._position:  # a retry sends the same item again
            self._position[(kind, item_id)] = self._counts[kind]
            self._counts[kind] += 1
        faults = self._faults[kind].get(self._position[(kind, item_id)])
        if faults:
            raise faults.popleft()


def make_client():
    backend = Backend()
    client = create_autospec(langsmith.Client, instance=True)
    client.backend = backend

    def has_dataset(*, dataset_name=None, dataset_id=None):
        return dataset_name in backend.datasets

    def read_dataset(*, dataset_name=None, dataset_id=None):
        return backend.datasets[dataset_name]

    def create_dataset(dataset_name, **kwargs):
        backend.datasets[dataset_name] = SimpleNamespace(id=uuid.uuid4(), name=dataset_name)
        return backend.datasets[dataset_name]

    def create_project(project_name, **kwargs):
        project = backend.projects.setdefault(
            project_name, SimpleNamespace(id=uuid.uuid4(), name=project_name)
        )
        project.kwargs = kwargs
        return project

    def create_example(**kwargs):
        key = str(kwargs["example_id"])
        backend.check("case", key)
        if key in backend.examples:
            raise LangSmithConflictError("example exists")
        backend.examples[key] = kwargs

    def update_example(example_id, **kwargs):
        backend.examples[str(example_id)].update(kwargs)

    def create_run(name, inputs, run_type, **kwargs):
        key = str(kwargs["id"])
        backend.check("trajectory" if kwargs.get("parent_run_id") is None else "step", key)
        backend.runs[key] = {"name": name, "inputs": inputs, "run_type": run_type, **kwargs}

    def create_feedback(run_id=None, key="unnamed", **kwargs):
        feedback_id = str(kwargs["feedback_id"])
        backend.check("score", feedback_id)
        if feedback_id in backend.feedback:
            raise LangSmithConflictError("feedback exists")
        backend.feedback[feedback_id] = {"run_id": run_id, "key": key, **kwargs}

    def update_feedback(feedback_id, **kwargs):
        backend.feedback[str(feedback_id)].update(kwargs)

    client.has_dataset.side_effect = has_dataset
    client.read_dataset.side_effect = read_dataset
    client.create_dataset.side_effect = create_dataset
    client.create_project.side_effect = create_project
    client.create_example.side_effect = create_example
    client.update_example.side_effect = update_example
    client.create_run.side_effect = create_run
    client.create_feedback.side_effect = create_feedback
    client.update_feedback.side_effect = update_feedback
    return client


def make_adapter(client=None, **kwargs):
    return LangSmithAdapter(
        client or make_client(), clock=lambda: START, sleep=lambda seconds: None, **kwargs
    )


def stored(adapter):
    """`{(target_kind, hex id): payload}`, the payload being the call's kwargs plus the few
    keys the conformance suite reads."""
    backend = adapter.client.backend
    found = {}
    for key, kwargs in backend.examples.items():
        found[("case", uuid.UUID(key).hex)] = dict(kwargs)
    for key, kwargs in backend.runs.items():
        metadata = kwargs["extra"]["metadata"]
        outputs = kwargs.get("outputs") or {}
        if kwargs.get("parent_run_id") is None:
            payload = {
                **kwargs,
                "final_output": outputs.get("output"),
                "final_state": outputs.get("state"),
                "repetition": metadata["assayer.repetition"],
            }
            found[("trajectory", uuid.UUID(key).hex)] = payload
        else:
            payload = {**kwargs, "kind": metadata["assayer.kind"]}
            found[("step", uuid.UUID(key).hex)] = payload
    for key, kwargs in backend.feedback.items():
        payload = {**kwargs, "name": kwargs["key"], "value": kwargs["score"]}
        found[("score", uuid.UUID(key).hex)] = payload
    return found


class TestLangSmithConformance(AdapterConformance):
    def make_adapter(self):
        return make_adapter()

    def inject(self, adapter, target_kind, *errors, nth=0):
        adapter.client.backend.fail_on(target_kind, errors, nth)

    def stored(self, adapter):
        return stored(adapter)


def _tool_then_model(value):
    return Trajectory(
        steps=[
            Step(kind="retrieval", id="r", name="search", input=value, output=["doc"]),
            Step(
                kind="model",
                id="m",
                parent_id="r",
                model="gpt-x",
                input=value,
                output="answer",
                usage=TokenUsage(10, 5, None),
            ),
            Step(kind="tool", id="t", name="calc", input={"x": 1}, output=2, error="boom"),
            Step(kind="other", id="o"),
        ],
        final_output="answer",
    )


def _exact(trajectory, case):
    return Detailed(1.0, comment="why", metadata={"k": "v"})


@pytest.fixture
def adapter():
    return make_adapter()


@pytest.fixture
def exported(adapter):
    runner = Runner(
        _tool_then_model,
        [Metric(name="judged", level="trajectory", fn=_exact)],
        adapter=adapter,
        pricing=PricingConfig(cost_per_input_token=1e-6, cost_per_output_token=2e-6),
    )
    experiment = runner.run(Dataset("d", [Case(input="q", id="c1", expected_output="answer")]))
    experiment.scores.append(Score("overall", 0.5, target="experiment", field="f"))
    assert runner.export(experiment).ok
    return experiment, adapter.client.backend


def _uuid(hex_id):
    return str(uuid.UUID(hex_id))


class TestRunTrees:
    def test_runs_form_a_tree_with_client_ids_and_dotted_order(self, exported):
        _, backend = exported
        root = next(r for r in backend.runs.values() if r.get("parent_run_id") is None)
        children = [r for r in backend.runs.values() if r is not root]

        assert len(children) == 4
        assert root["trace_id"] == root["id"]
        assert root["dotted_order"].endswith(str(root["id"]))
        assert root["dotted_order"].startswith("20261017T120000000000Z")
        for child in children:
            assert child["trace_id"] == root["id"]
            assert isinstance(child["id"], uuid.UUID)
            assert child["dotted_order"].endswith(str(child["id"]))
        assert all(child["dotted_order"] > root["dotted_order"] for child in children)
        orders = [c["dotted_order"] for c in sorted(children, key=lambda c: c["start_time"])]
        assert orders == sorted(orders)

    def test_a_step_with_parent_nests_under_it(self, exported):
        _, backend = exported
        by_name = {r["name"]: r for r in backend.runs.values()}
        search, model = by_name["search"], by_name["gpt-x"]

        assert model["parent_run_id"] == search["id"]
        assert model["dotted_order"].startswith(search["dotted_order"] + ".")
        root = next(r for r in backend.runs.values() if r.get("parent_run_id") is None)
        assert search["parent_run_id"] == root["id"]

    def test_kind_maps_to_run_type(self, exported):
        _, backend = exported
        by_name = {r["name"]: r["run_type"] for r in backend.runs.values()}

        assert by_name["search"] == "retriever"
        assert by_name["gpt-x"] == "llm"
        assert by_name["calc"] == "tool"
        assert by_name["other"] == "chain"
        root = next(r for r in backend.runs.values() if r.get("parent_run_id") is None)
        assert root["run_type"] == "chain"

    def test_runs_go_to_the_experiment_project_and_link_to_the_case(self, exported):
        experiment, backend = exported
        root = next(r for r in backend.runs.values() if r.get("parent_run_id") is None)
        (example_id,) = backend.examples

        assert root["project_name"] == experiment.name
        assert root["reference_example_id"] == uuid.UUID(example_id)
        assert root["inputs"] == {"input": "q"}
        assert root["outputs"] == {"output": "answer", "state": None}

    def test_model_steps_carry_tokens_and_trajectories_carry_cost(self, exported):
        _, backend = exported
        by_name = {r["name"]: r for r in backend.runs.values()}

        assert by_name["gpt-x"]["outputs"]["usage_metadata"] == {
            "input_tokens": 10,
            "output_tokens": 5,
            "total_tokens": 15,
        }
        assert by_name["gpt-x"]["extra"]["metadata"]["ls_model_name"] == "gpt-x"
        root = next(r for r in backend.runs.values() if r.get("parent_run_id") is None)
        usage = root["extra"]["metadata"]["assayer.usage"]
        assert (usage["input_tokens"], usage["output_tokens"]) == (10, 5)
        assert usage["cost_usd"] == pytest.approx(2e-5)

    def test_step_cost_is_exported_when_known(self, adapter):
        runner = Runner(
            lambda v: Trajectory(
                steps=[Step(kind="model", model="m", usage=TokenUsage(1, 1, 0.25))]
            ),
            adapter=adapter,
        )
        runner.export(runner.run(Dataset("d", [Case(input="a", id="c1")])))

        (step,) = (r for r in adapter.client.backend.runs.values() if r["run_type"] == "llm")
        assert step["outputs"]["usage_metadata"]["total_cost"] == 0.25

    def test_step_error_is_sent_and_the_run_ends(self, exported):
        _, backend = exported
        calc = next(r for r in backend.runs.values() if r["name"] == "calc")

        assert calc["error"] == "boom"
        assert calc["end_time"] >= calc["start_time"]
        assert calc["inputs"] == {"x": 1}

    def test_unknown_parent_falls_back_to_the_root_and_is_noted(self, adapter):
        runner = Runner(
            lambda v: Trajectory(steps=[Step(kind="tool", id="a", parent_id="ghost")]),
            adapter=adapter,
        )

        report = runner.export(runner.run(Dataset("d", [Case(input="a", id="c1")])))

        assert report.ok
        assert any("parent" in note for note in report.notes)
        runs = adapter.client.backend.runs.values()
        assert {r["trace_id"] for r in runs} == {next(iter(runs))["trace_id"]}

    def test_a_step_whose_trajectory_failed_is_a_validation_failure(self, adapter):
        runner = Runner(_tool_then_model, adapter=adapter)
        experiment = runner.run(Dataset("d", [Case(input="a", id="c1")]))
        adapter.client.backend.fail_on("trajectory", [AdapterCallError("validation", "bad run")], 0)

        report = runner.export(experiment)

        assert {(f.target_kind, f.kind) for f in report.failed} == {
            ("trajectory", "validation"),
            ("step", "validation"),
        }

    def test_runs_are_queued_and_the_client_is_flushed(self, adapter):
        runner = Runner(_tool_then_model, adapter=adapter)
        experiment = runner.run(Dataset("d", [Case(input="a", id="c1")]))

        report = runner.export(experiment)

        assert {i.target_kind for i in report.queued} == {"trajectory", "step"}
        assert {i.target_kind for i in report.confirmed} == {"case"}
        adapter.client.flush.assert_called_once_with()


class TestScores:
    def test_feedback_is_named_metric_dot_field_with_the_field_in_metadata(self, exported):
        _, backend = exported
        by_key = {f["key"]: f for f in backend.feedback.values()}

        assert set(by_key) == {"judged", "overall.f"}
        assert by_key["overall.f"]["extra"]["field"] == "f"
        assert by_key["judged"]["extra"]["k"] == "v"
        assert "field" not in by_key["judged"]["extra"]

    def test_feedback_carries_score_comment_and_label(self, exported):
        _, backend = exported
        judged = next(f for f in backend.feedback.values() if f["key"] == "judged")

        assert judged["score"] == 1.0
        assert judged["comment"] == "why"

    def test_label_is_the_feedback_value(self, adapter):
        runner = Runner(lambda v: v, adapter=adapter)
        experiment = runner.run(Dataset("d", [Case(input="a", id="c1")]))
        experiment.scores.append(Score("verdict", 1.0, label="pass", target="experiment"))

        runner.export(experiment)

        (feedback,) = adapter.client.backend.feedback.values()
        assert feedback["value"] == "pass"

    def test_trajectory_and_step_scores_attach_to_their_runs(self, adapter):
        def per_step(step, case):
            return 1.0

        runner = Runner(
            _tool_then_model,
            [
                Metric(name="t", level="trajectory", fn=lambda t, c: 1.0),
                Metric(name="s", level="step", fn=per_step),
            ],
            adapter=adapter,
        )
        runner.export(runner.run(Dataset("d", [Case(input="a", id="c1")])))
        backend = adapter.client.backend
        project = next(iter(backend.projects.values()))
        root = next(r for r in backend.runs.values() if r.get("parent_run_id") is None)

        for feedback in backend.feedback.values():
            assert feedback["session_id"] == project.id
            assert str(feedback["run_id"]) in {str(k) for k in backend.runs}
        trajectory = next(f for f in backend.feedback.values() if f["key"] == "t")
        assert trajectory["run_id"] == root["id"]
        assert len([f for f in backend.feedback.values() if f["key"] == "s"]) == 4

    def test_experiment_level_scores_attach_to_the_experiment_project(self, exported):
        experiment, backend = exported
        overall = next(f for f in backend.feedback.values() if f["key"] == "overall.f")

        assert overall["run_id"] is None
        assert overall["project_id"] == backend.projects[experiment.name].id
        assert overall["score"] == 0.5

    def test_an_unlinked_score_goes_to_the_project_and_keeps_its_target(self, adapter):
        runner = Runner(lambda v: v, adapter=adapter)
        experiment = runner.run(Dataset("d", [Case(input="a", id="c1")]))
        experiment.scores.append(Score("orphan", 1.0, target="step", target_id="nowhere"))

        runner.export(experiment)

        (feedback,) = adapter.client.backend.feedback.values()
        assert feedback["run_id"] is None
        assert feedback["extra"]["target"] == "step"

    def test_a_repeated_export_updates_the_feedback(self, exported, adapter):
        experiment, backend = exported
        experiment.scores[-1] = Score("overall", 0.75, target="experiment", field="f")

        report = Runner(adapter=adapter).export(experiment)

        assert report.ok
        adapter.client.update_feedback.assert_called()
        overall = next(f for f in backend.feedback.values() if f["key"] == "overall.f")
        assert overall["score"] == 0.75


class TestCases:
    def test_dataset_and_experiment_project_are_created_once_and_linked(self, exported):
        experiment, backend = exported

        assert list(backend.datasets) == [experiment.name]
        project = backend.projects[experiment.name]
        assert project.kwargs["reference_dataset_id"] == backend.datasets[experiment.name].id
        assert project.kwargs["upsert"] is True

    def test_dataset_name_can_be_chosen(self):
        adapter = make_adapter(dataset_name="shared")
        runner = Runner(lambda v: v, adapter=adapter)

        runner.export(runner.run(Dataset("d", [Case(input="a", id="c1")])))

        assert list(adapter.client.backend.datasets) == ["shared"]

    def test_an_existing_dataset_is_reused(self, adapter):
        runner = Runner(lambda v: v, adapter=adapter)
        experiment = runner.run(Dataset("d", [Case(input="a", id="c1")]))
        runner.export(experiment)
        runner.export(experiment)

        adapter.client.create_dataset.assert_called_once()

    def test_examples_hold_the_case_and_its_reference(self, exported):
        _, backend = exported
        (example,) = backend.examples.values()

        assert example["inputs"] == {"input": "q"}
        assert example["outputs"] == {"output": "answer"}
        assert example["metadata"]["case_id"] == "c1"
        assert example["dataset_id"] == next(iter(backend.datasets.values())).id

    def test_a_case_that_exists_is_updated_and_nothing_is_ever_deleted(self, adapter):
        runner = Runner(lambda v: v, adapter=adapter)
        experiment = runner.run(Dataset("d", [Case(input="a", id="c1")]))
        runner.export(experiment)
        experiment.cases[0].input = "changed"

        report = runner.export(experiment)

        assert report.ok
        adapter.client.update_example.assert_called_once()
        (example,) = adapter.client.backend.examples.values()
        assert example["inputs"] == {"input": "changed"}
        adapter.client.delete_example.assert_not_called()
        adapter.client.delete_dataset.assert_not_called()

    def test_without_content_an_existing_example_keeps_its_inputs(self, adapter):
        runner = Runner(lambda v: v, adapter=adapter)
        experiment = runner.run(Dataset("d", [Case(input="a", id="c1")]))
        runner.export(experiment)

        runner.export(experiment, include_content=False)

        (example,) = adapter.client.backend.examples.values()
        assert example["inputs"] == {"input": "a"}

    def test_a_dataset_with_no_cases_creates_nothing(self, adapter):
        report = adapter.export(Runner(lambda v: v).run(Dataset("d", [])))

        assert report.ok
        assert adapter.client.backend.datasets == {}


class TestCredentials:
    @pytest.fixture(autouse=True)
    def clean_env(self, monkeypatch):
        monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
        monkeypatch.delenv("LANGCHAIN_API_KEY", raising=False)

    def test_no_credentials_is_a_config_error(self):
        with patch("assayer.integrations.langsmith_adapter.langsmith.Client") as client:
            with pytest.raises(AdapterConfigError, match="LANGSMITH_API_KEY"):
                LangSmithAdapter()
        client.assert_not_called()

    def test_reads_langsmith_api_key(self, monkeypatch):
        monkeypatch.setenv("LANGSMITH_API_KEY", "new")
        monkeypatch.setenv("LANGCHAIN_API_KEY", "old")
        with patch("assayer.integrations.langsmith_adapter.langsmith.Client") as client:
            LangSmithAdapter()
        client.assert_called_once_with(api_key="new")

    def test_falls_back_to_langchain_api_key(self, monkeypatch):
        monkeypatch.setenv("LANGCHAIN_API_KEY", "old")
        with patch("assayer.integrations.langsmith_adapter.langsmith.Client") as client:
            LangSmithAdapter()
        client.assert_called_once_with(api_key="old")

    def test_an_explicit_api_key_wins(self, monkeypatch):
        monkeypatch.setenv("LANGSMITH_API_KEY", "env")
        with patch("assayer.integrations.langsmith_adapter.langsmith.Client") as client:
            LangSmithAdapter(api_key="given")
        client.assert_called_once_with(api_key="given")

    def test_an_injected_client_needs_no_key(self):
        client = make_client()

        assert LangSmithAdapter(client).client is client

    def test_empty_names_are_config_errors(self):
        with pytest.raises(AdapterConfigError):
            LangSmithAdapter(make_client(), name=" ")
        with pytest.raises(AdapterConfigError):
            LangSmithAdapter(make_client(), dataset_name=" ")

    def test_close_closes_a_client_it_created_but_not_one_it_was_given(self, monkeypatch):
        monkeypatch.setenv("LANGSMITH_API_KEY", "k")
        with patch("assayer.integrations.langsmith_adapter.langsmith.Client") as factory:
            LangSmithAdapter().close()
        factory.return_value.close.assert_called_once()

        given = make_client()
        with LangSmithAdapter(given):
            pass
        given.close.assert_not_called()


class TestErrorMapping:
    @pytest.mark.parametrize(
        ("error", "kind", "retryable"),
        [
            (LangSmithAuthError("no"), "auth", False),
            (LangSmithRateLimitError("slow"), "rate_limited", True),
            (LangSmithConnectionError("down"), "transport", True),
            (langsmith.utils.LangSmithAPIError("500"), "transport", True),
            (langsmith.utils.LangSmithNotFoundError("gone"), "validation", False),
            (langsmith.utils.LangSmithUserError("bad"), "validation", False),
            (langsmith.utils.LangSmithError("?"), "unknown", False),
            (ValueError("odd"), "unknown", False),
        ],
    )
    def test_sdk_errors_become_taxonomy_failures(self, adapter, error, kind, retryable):
        adapter.client.create_example.side_effect = error
        runner = Runner(lambda v: v, adapter=adapter)
        experiment = runner.run(Dataset("d", [Case(input="a", id="c1")]))

        (failure,) = runner.export(experiment).failed

        assert (failure.target_kind, failure.kind, failure.retryable) == ("case", kind, retryable)

    def test_a_failed_flush_is_noted_not_raised(self, adapter):
        adapter.client.flush.side_effect = RuntimeError("down")
        runner = Runner(lambda v: v, adapter=adapter)

        report = runner.export(runner.run(Dataset("d", [Case(input="a", id="c1")])))

        assert report.ok
        assert any("flush" in note for note in report.notes)

    def test_setup_is_retried_on_the_next_item_after_it_failed(self, adapter):
        calls = iter([LangSmithConnectionError("down")] * 3)

        def flaky(*args, **kwargs):
            try:
                raise next(calls)
            except StopIteration:
                return SimpleNamespace(id=uuid.uuid4(), name="d")

        adapter.client.has_dataset.side_effect = lambda **kwargs: False
        adapter.client.create_dataset.side_effect = flaky
        runner = Runner(lambda v: v, adapter=adapter)
        experiment = runner.run(Dataset("d", [Case(input="a", id="c1"), Case(input="b", id="c2")]))

        report = runner.export(experiment)

        assert [f.target_kind for f in report.failed] == ["case"]
        assert len([i for i in report.confirmed if i.target_kind == "case"]) == 1


@pytest.mark.skipif(
    not (os.environ.get("LANGSMITH_API_KEY") or os.environ.get("LANGCHAIN_API_KEY")),
    reason="needs LANGSMITH_API_KEY (or LANGCHAIN_API_KEY): exports to the real LangSmith",
)
def test_live_smoke():
    name = f"assayer-smoke-{uuid.uuid4().hex[:8]}"
    runner = Runner(
        _tool_then_model,
        [Metric(name="exact", level="trajectory", fn=lambda t, c: 1.0)],
        adapter=LangSmithAdapter(),
    )
    experiment = runner.run(Dataset(name, [Case(input="q", id="c1", expected_output="answer")]))
    experiment.name = name

    with runner.adapter:
        report = runner.export(experiment)

    assert report.ok, report.failed
