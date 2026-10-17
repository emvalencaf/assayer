"""LangfuseAdapter, held to the shared conformance suite, plus what is its own.

The client is `create_autospec(Langfuse)` backed by a small in-memory `Backend`, so every call is
checked against the real signatures. `test_live_smoke` runs only with credentials.
"""

import datetime as dt
import hashlib
import inspect
import json
import os
import time
import uuid
from collections import defaultdict, deque
from types import SimpleNamespace
from unittest.mock import create_autospec

import httpx
import pytest
from langfuse import Langfuse
from langfuse.api import (
    AccessDeniedError,
    BadRequestError,
    InternalServerError,
    LangfuseAPI,
    NotFoundError,
    UnauthorizedError,
)
from langfuse.api.core.api_error import ApiError

from assayer.adapters import AdapterCallError, AdapterConfigError, trajectory_id
from assayer.integrations.langfuse_adapter import LangfuseAdapter
from assayer.metrics.metric import Detailed, Metric
from assayer.models import Case, Dataset, PricingConfig, Score, Step, TokenUsage, Trajectory
from assayer.runner import Runner

from ..adapters.conformance import AdapterConformance

START = dt.datetime(2026, 10, 17, 12, 0, 0, tzinfo=dt.UTC)
START_NANOS = int(START.timestamp()) * 1_000_000_000


class Backend:
    """What Langfuse would hold after the calls, keyed by the ids the adapter chose."""

    def __init__(self):
        self.datasets = {}
        self.items = {}
        self.spans = {}
        self.scores = {}
        self.headers = []
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


def _value(attribute):
    value = attribute.value
    for name in ("string_value", "int_value", "double_value", "bool_value"):
        if getattr(value, name) is not None:
            return getattr(value, name)
    return None


def _decode(value):
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return value


def make_client():
    backend = Backend()
    client = create_autospec(Langfuse, instance=True)
    client.api = create_autospec(LangfuseAPI, instance=True)
    client.backend = backend

    def create_dataset(*, name, description=None, metadata=None, **kwargs):
        dataset = backend.datasets.setdefault(name, SimpleNamespace(id=f"ds-{name}", name=name))
        dataset.kwargs = {"description": description, "metadata": metadata}
        return dataset

    def create_dataset_item(*, dataset_name, id=None, **kwargs):
        backend.check("case", id)
        backend.items[id] = {"dataset_name": dataset_name, "id": id, **kwargs}

    def export_traces(*, resource_spans, request_options=None):
        backend.headers.append((request_options or {}).get("additional_headers"))
        for resource_span in resource_spans:
            for scope_span in resource_span.scope_spans:
                for span in scope_span.spans:
                    attributes = {a.key: _value(a) for a in span.attributes}
                    kind = "trajectory" if span.parent_span_id is None else "step"
                    key = (span.trace_id, span.span_id)
                    backend.check(kind, key)
                    backend.spans[key] = {
                        "name": span.name,
                        "parent_span_id": span.parent_span_id,
                        "start": int(span.start_time_unix_nano),
                        "end": int(span.end_time_unix_nano),
                        "status": span.status,
                        "attributes": attributes,
                    }

    def create_score(**kwargs):
        backend.check("score", kwargs["score_id"])
        backend.scores[kwargs["score_id"]] = kwargs

    client.create_dataset.side_effect = create_dataset
    client.create_dataset_item.side_effect = create_dataset_item
    client.api.opentelemetry.export_traces.side_effect = export_traces
    client.api.projects.get.return_value = SimpleNamespace(data=[SimpleNamespace(id="proj-1")])
    client.create_score.side_effect = create_score
    return client


def make_adapter(client=None, **kwargs):
    return LangfuseAdapter(
        client or make_client(), clock=lambda: START, sleep=lambda seconds: None, **kwargs
    )


def _metadata(span, prefix="langfuse.observation.metadata."):
    return {
        key.removeprefix(prefix): _decode(value)
        for key, value in span["attributes"].items()
        if key.startswith(prefix)
    }


def stored(adapter):
    """`{(target_kind, hex id): payload}`, the payload being what was sent plus the few keys the
    conformance suite reads."""
    backend = adapter.client.backend
    found = {}
    for item in backend.items.values():
        metadata = item["metadata"]
        key = ("case", metadata["assayer.id"])
        found[key] = dict(item)
    for span in backend.spans.values():
        metadata = _metadata(span)
        key = ("trajectory" if span["parent_span_id"] is None else "step", metadata["assayer.id"])
        found[key] = {
            **span,
            **metadata,
            "kind": metadata.get("assayer.kind"),
            "repetition": metadata.get("assayer.repetition"),
        }
    for score in backend.scores.values():
        found[("score", score["metadata"]["assayer.id"])] = dict(score, name=score["name"])
    return found


class TestLangfuseConformance(AdapterConformance):
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
        final_state={"done": True},
        session_id="s1",
    )


def _judged(trajectory, case):
    return Detailed(1.0, comment="why", metadata={"k": "v"})


def _run(adapter, **kwargs):
    runner = Runner(
        _tool_then_model,
        [Metric(name="judged", level="trajectory", fn=_judged)],
        adapter=adapter,
        pricing=PricingConfig(cost_per_input_token=1e-6, cost_per_output_token=2e-6),
        **kwargs,
    )
    experiment = runner.run(Dataset("d", [Case(input="q", id="c1", expected_output="answer")]))
    return runner, experiment


@pytest.fixture
def adapter():
    return make_adapter()


@pytest.fixture
def exported(adapter):
    runner, experiment = _run(adapter, repetitions=2)
    experiment.scores.append(Score("overall", 0.5, target="experiment", field="f"))
    assert runner.export(experiment).ok
    return experiment, adapter.client.backend


def _by_name(backend):
    return {span["name"]: span for span in backend.spans.values() if span["parent_span_id"]}


def _roots(backend):
    return [span for span in backend.spans.values() if span["parent_span_id"] is None]


class TestDataset:
    def test_the_dataset_is_synced_by_name_once_per_export(self, exported):
        _, backend = exported

        assert list(backend.datasets) == ["d"]
        assert backend.datasets["d"].kwargs["metadata"] == {"source": "assayer"}

    def test_dataset_name_overrides_the_experiment_name(self):
        adapter = make_adapter(dataset_name="shared")
        runner, experiment = _run(adapter)

        runner.export(experiment)

        assert list(adapter.client.backend.datasets) == ["shared"]
        (item,) = adapter.client.backend.items.values()
        assert item["dataset_name"] == "shared"

    def test_item_id_is_the_case_id(self, exported):
        _, backend = exported

        (item,) = backend.items.values()

        assert item["id"] == "c1"
        assert item["input"] == "q"
        assert item["expected_output"] == "answer"
        assert item["metadata"]["case_id"] == "c1"

    def test_without_content_the_item_has_no_input(self, adapter):
        runner, experiment = _run(adapter)

        runner.export(experiment, include_content=False)

        (item,) = adapter.client.backend.items.values()
        assert "input" not in item and "expected_output" not in item


class TestObservations:
    def test_ids_are_deterministic_and_the_trace_id_is_the_trajectory_id(self, exported):
        _experiment, backend = exported

        assert all(len(trace) == 32 and len(span) == 16 for trace, span in backend.spans)
        assert len({trace for trace, _ in backend.spans}) == 2  # one trace per repetition

    def test_steps_nest_under_their_parent_or_the_root(self, exported):
        _, backend = exported
        roots = {
            key[0]: key[1] for key, span in backend.spans.items() if not span["parent_span_id"]
        }
        search = {key[0]: key[1] for key, s in backend.spans.items() if s["name"] == "search"}

        for (trace, _), span in backend.spans.items():
            if span["name"] == "search":
                assert span["parent_span_id"] == roots[trace]
            if span["name"] == "gpt-x":
                assert span["parent_span_id"] == search[trace]

    def test_kind_maps_to_observation_type(self, exported):
        _, backend = exported
        types = {
            name: span["attributes"]["langfuse.observation.type"]
            for name, span in _by_name(backend).items()
        }

        assert types == {
            "search": "retriever",
            "gpt-x": "generation",
            "calc": "tool",
            "other": "span",
        }
        assert {r["attributes"]["langfuse.observation.type"] for r in _roots(backend)} == {"span"}

    def test_model_steps_carry_model_tokens_and_cost(self, adapter):
        runner = Runner(
            lambda v: Trajectory(
                steps=[Step(kind="model", model="m", usage=TokenUsage(10, 5, 0.25))]
            ),
            adapter=adapter,
        )
        runner.export(runner.run(Dataset("d", [Case(input="a", id="c1")])))

        (step,) = _by_name(adapter.client.backend).values()
        attributes = step["attributes"]

        assert attributes["langfuse.observation.model.name"] == "m"
        assert json.loads(attributes["langfuse.observation.usage_details"]) == {
            "input": 10,
            "output": 5,
            "total": 15,
        }
        assert json.loads(attributes["langfuse.observation.cost_details"]) == {"total": 0.25}

    def test_a_trajectory_carries_its_total_usage(self, exported):
        _, backend = exported
        usage = _metadata(_roots(backend)[0])["assayer.usage"]

        assert (usage["input_tokens"], usage["output_tokens"]) == (10, 5)
        assert usage["cost_usd"] == pytest.approx(2e-5)

    def test_step_error_marks_the_observation(self, exported):
        _, backend = exported
        calc = _by_name(backend)["calc"]

        assert calc["attributes"]["langfuse.observation.level"] == "ERROR"
        assert calc["attributes"]["langfuse.observation.status_message"] == "boom"
        assert calc["status"]["code"] == 2
        assert json.loads(calc["attributes"]["langfuse.observation.input"]) == {"x": 1}

    def test_final_output_and_state_are_trajectory_metadata(self, exported):
        _, backend = exported

        for root in _roots(backend):
            for prefix in ("langfuse.observation.metadata.", "langfuse.trace.metadata."):
                metadata = _metadata(root, prefix)
                assert metadata["final_output"] == "answer"
                assert metadata["final_state"] == {"done": True}
            assert root["attributes"]["langfuse.observation.output"] == "answer"
            assert root["attributes"]["session.id"] == "s1"

    def test_timing_is_synthetic_and_keeps_the_steps_in_order(self, exported):
        _, backend = exported
        root = _roots(backend)[0]
        steps = sorted(_by_name(backend).values(), key=lambda s: s["start"])

        assert root["start"] == START_NANOS
        assert all(root["start"] < s["start"] <= root["end"] for s in steps)
        assert [s["name"] for s in steps][:2] == ["search", "gpt-x"]
        assert root["attributes"]["langfuse.observation.metadata.assayer.synthetic_timing"] is True

    def test_started_at_fixes_the_time_across_adapters(self):
        other = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
        adapter = make_adapter(started_at=other)
        runner, experiment = _run(adapter)

        runner.export(experiment)

        assert _roots(adapter.client.backend)[0]["start"] == int(other.timestamp()) * 10**9

    def test_unknown_parent_falls_back_to_the_root_and_is_noted(self, adapter):
        runner = Runner(
            lambda v: Trajectory(steps=[Step(kind="tool", id="a", parent_id="ghost")]),
            adapter=adapter,
        )

        report = runner.export(runner.run(Dataset("d", [Case(input="a", id="c1")])))

        assert report.ok
        assert any("parent" in note for note in report.notes)
        (key,) = (k for k, s in adapter.client.backend.spans.items() if s["parent_span_id"])
        (root_key,) = (
            k for k, s in adapter.client.backend.spans.items() if not s["parent_span_id"]
        )
        assert adapter.client.backend.spans[key]["parent_span_id"] == root_key[1]

    def test_a_step_whose_trajectory_failed_is_a_validation_failure(self, adapter):
        runner, experiment = _run(adapter)
        adapter.client.backend.fail_on("trajectory", [AdapterCallError("validation", "bad")], 0)

        report = runner.export(experiment)

        assert {(f.target_kind, f.kind) for f in report.failed} >= {
            ("trajectory", "validation"),
            ("step", "validation"),
        }

    def test_spans_are_confirmed_and_sent_with_the_ingestion_version_header(self, adapter):
        runner, experiment = _run(adapter)

        report = runner.export(experiment)

        assert {i.target_kind for i in report.confirmed} == {"case", "trajectory", "step"}
        assert {i.target_kind for i in report.queued} == {"score"}
        assert {h["x-langfuse-ingestion-version"] for h in adapter.client.backend.headers} == {"4"}


class TestDatasetRuns:
    def test_one_run_per_repetition_named_after_the_experiment(self, exported):
        experiment, backend = exported
        runs = {r["attributes"]["langfuse.experiment.name"] for r in _roots(backend)}

        assert runs == {f"{experiment.name}/rep-0", f"{experiment.name}/rep-1"}

    def test_every_observation_carries_the_run_the_item_and_the_dataset(self, exported):
        _, backend = exported

        for (_trace, _span_id), span in backend.spans.items():
            attributes = span["attributes"]
            assert attributes["langfuse.experiment.item.id"] == "c1"
            assert attributes["langfuse.experiment.dataset.id"] == "ds-d"
            assert attributes["langfuse.environment"] == "sdk-experiment"
        by_run = defaultdict(set)
        for span in backend.spans.values():
            by_run[span["attributes"]["langfuse.experiment.name"]].add(
                span["attributes"]["langfuse.experiment.id"]
            )
        assert all(len(ids) == 1 for ids in by_run.values())
        assert len({next(iter(ids)) for ids in by_run.values()}) == 2

    def test_the_run_id_follows_the_sdk_derivation(self, exported):
        experiment, backend = exported
        root = next(
            r for r in _roots(backend) if r["attributes"]["langfuse.experiment.name"].endswith("0")
        )
        payload = json.dumps(
            ["langfuse-experiment-v1", "proj-1", "ds-d", f"{experiment.name}/rep-0"],
            separators=(",", ":"),
            ensure_ascii=False,
        )

        assert (
            root["attributes"]["langfuse.experiment.id"]
            == hashlib.sha256(payload.encode()).hexdigest()[:16]
        )

    def test_the_root_observation_is_marked_as_the_items_root(self, exported):
        _, backend = exported

        for (_trace, span_id), span in backend.spans.items():
            if span["parent_span_id"] is None:
                attributes = span["attributes"]
                assert attributes["langfuse.experiment.item.root_observation_id"] == span_id


class TestUnlinked:
    def test_a_trajectory_without_a_case_id_does_not_point_at_a_dataset_item(self, adapter):
        runner = Runner(_tool_then_model, adapter=adapter)
        experiment = runner.run(Dataset("d", [Case(input="a", id="c1")]))
        experiment.trajectories[0].case_id = None

        runner.export(experiment)

        (root,) = _roots(adapter.client.backend)
        assert "langfuse.experiment.dataset.id" not in root["attributes"]

    def test_an_unresolvable_project_is_a_validation_failure_of_the_trajectory(self, adapter):
        adapter.client.api.projects.get.return_value = SimpleNamespace(data=[])
        runner, experiment = _run(adapter)

        report = runner.export(experiment)

        assert ("trajectory", "validation") in {(f.target_kind, f.kind) for f in report.failed}


class TestScores:
    def test_scores_are_numeric_and_target_the_trace_or_the_observation(self, adapter):
        runner = Runner(
            _tool_then_model,
            [
                Metric(name="traj", level="trajectory", fn=lambda t, c: 1.0),
                Metric(name="step", level="step", fn=lambda s, c: 0.5),
            ],
            adapter=adapter,
        )
        experiment = runner.run(Dataset("d", [Case(input="q", id="c1")]))

        runner.export(experiment)

        backend = adapter.client.backend
        (root_key,) = (k for k, s in backend.spans.items() if not s["parent_span_id"])
        traj = next(s for s in backend.scores.values() if s["name"] == "traj")
        steps = [s for s in backend.scores.values() if s["name"] == "step"]
        assert traj["trace_id"] == root_key[0]
        assert traj["data_type"] == "NUMERIC" and traj["value"] == 1.0
        assert "observation_id" not in traj or traj["observation_id"] is None
        step_span_ids = {k[1] for k, s in backend.spans.items() if s["parent_span_id"]}
        assert {s["observation_id"] for s in steps} == step_span_ids
        assert {s["trace_id"] for s in steps} == {root_key[0]}

    def test_score_ids_are_the_export_ids_and_run_scores_add_the_repetition(self, exported):
        _, backend = exported

        for score_id, score in backend.scores.items():
            export_id = score["metadata"]["assayer.id"]
            assert score_id in (export_id, f"{export_id}-rep-0", f"{export_id}-rep-1")

    def test_comment_label_and_metadata_are_sent(self, exported):
        _, backend = exported
        judged = next(s for s in backend.scores.values() if s["name"] == "judged")

        assert judged["comment"] == "why"
        assert judged["metadata"]["k"] == "v"
        assert judged["metadata"]["assayer.target"] == "trajectory"

    def test_a_field_is_part_of_the_score_name(self, exported):
        _, backend = exported

        assert "overall.f" in {s["name"] for s in backend.scores.values()}

    def test_an_experiment_score_goes_to_every_dataset_run(self, exported):
        _, backend = exported
        overall = [s for s in backend.scores.values() if s["name"] == "overall.f"]
        run_ids = {r["attributes"]["langfuse.experiment.id"] for r in _roots(backend)}

        assert {s["dataset_run_id"] for s in overall} == run_ids
        assert len(overall) == 2
        assert all("trace_id" not in s for s in overall)

    def test_metadata_is_dropped_and_noted_when_the_sdk_does_not_accept_it(self, adapter):
        def create_score(
            *, name, value, trace_id=None, observation_id=None, score_id=None,
            data_type=None, comment=None, dataset_run_id=None, session_id=None,
        ):  # fmt: skip
            adapter.client.backend.scores[score_id] = {"name": name, "value": value}

        adapter.client.create_score = create_autospec(create_score)
        adapter.client.create_score.side_effect = create_score
        runner, experiment = _run(adapter)

        report = runner.export(experiment)

        assert report.ok
        assert adapter.client.backend.scores
        assert any("metadata" in note for note in report.notes)

    def test_nothing_is_noted_when_the_sdk_accepts_metadata(self, adapter):
        runner, experiment = _run(adapter)

        assert not any("metadata" in n for n in runner.export(experiment).notes)
        assert "metadata" in inspect.signature(adapter.client.create_score).parameters


class TestErrors:
    @pytest.mark.parametrize(
        ("error", "kind", "retryable"),
        [
            (UnauthorizedError(body=None), "auth", False),
            (AccessDeniedError(body=None), "auth", False),
            (ApiError(status_code=429, headers={"retry-after": "7"}), "rate_limited", True),
            (InternalServerError(body=None), "transport", True),
            (httpx.ConnectError("down"), "transport", True),
            (httpx.ReadTimeout("slow"), "transport", True),
            (BadRequestError(body=None), "validation", False),
            (NotFoundError(body=None), "validation", False),
            (ApiError(status_code=422), "validation", False),
            (ApiError(status_code=None), "unknown", False),
            (ValueError("odd"), "unknown", False),
        ],
    )
    def test_sdk_errors_become_taxonomy_failures(self, adapter, error, kind, retryable):
        adapter.client.create_dataset_item.side_effect = error
        runner = Runner(lambda v: v, adapter=adapter)
        experiment = runner.run(Dataset("d", [Case(input="a", id="c1")]))

        (failure,) = runner.export(experiment).failed

        assert (failure.target_kind, failure.kind, failure.retryable) == ("case", kind, retryable)

    def test_the_retry_after_header_is_honored(self, adapter):
        waits = []
        adapter._sleep = waits.append
        calls = iter([ApiError(status_code=429, headers={"retry-after": "7"})])

        def flaky(**kwargs):
            try:
                raise next(calls)
            except StopIteration:
                return None

        adapter.client.create_dataset_item.side_effect = flaky
        runner = Runner(lambda v: v, adapter=adapter)

        report = runner.export(runner.run(Dataset("d", [Case(input="a", id="c1")])))

        assert report.ok
        assert waits == [7]

    def test_a_span_rejected_by_the_api_is_a_failure_of_that_step(self, adapter):
        adapter.client.api.opentelemetry.export_traces.side_effect = ApiError(status_code=400)
        runner, experiment = _run(adapter)

        report = runner.export(experiment)

        assert {f.target_kind for f in report.failed} == {"trajectory", "step"}

    def test_setup_is_retried_on_the_next_item_after_it_failed(self, adapter):
        calls = iter([httpx.ConnectError("down")] * 3)

        def flaky(**kwargs):
            try:
                raise next(calls)
            except StopIteration:
                return SimpleNamespace(id="ds", name="d")

        adapter.client.create_dataset.side_effect = flaky
        runner = Runner(lambda v: v, adapter=adapter)
        experiment = runner.run(Dataset("d", [Case(input="a", id="c1"), Case(input="b", id="c2")]))

        report = runner.export(experiment)

        assert [f.target_kind for f in report.failed] == ["case"]
        assert len([i for i in report.confirmed if i.target_kind == "case"]) == 1

    def test_scores_are_queued_and_the_client_is_flushed(self, adapter):
        runner, experiment = _run(adapter)

        runner.export(experiment)

        adapter.client.flush.assert_called_once_with()

    def test_a_failed_flush_is_noted_not_raised(self, adapter):
        adapter.client.flush.side_effect = RuntimeError("down")
        runner, experiment = _run(adapter)

        report = runner.export(experiment)

        assert report.ok
        assert any("flush" in note for note in report.notes)


class TestConfig:
    def test_a_name_and_dataset_name_must_not_be_empty(self):
        with pytest.raises(AdapterConfigError, match="name"):
            LangfuseAdapter(make_client(), name=" ")
        with pytest.raises(AdapterConfigError, match="dataset_name"):
            LangfuseAdapter(make_client(), dataset_name="")

    def test_started_at_needs_a_timezone(self):
        with pytest.raises(AdapterConfigError, match="timezone"):
            LangfuseAdapter(make_client(), started_at=dt.datetime(2026, 1, 1))

    def test_without_a_client_and_keys_it_is_a_config_error(self, monkeypatch):
        monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
        monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

        with pytest.raises(AdapterConfigError, match="LANGFUSE_PUBLIC_KEY"):
            LangfuseAdapter()

    def test_the_adapter_builds_its_client_from_the_environment(self, monkeypatch):
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk")
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk")
        built = []
        monkeypatch.setattr(
            "assayer.integrations.langfuse_adapter.Langfuse",
            lambda **kwargs: built.append(kwargs) or create_autospec(Langfuse, instance=True),
        )

        adapter = LangfuseAdapter(base_url="https://example.test")

        assert built == [
            {"public_key": "pk", "secret_key": "sk", "base_url": "https://example.test"}
        ]
        adapter.close()
        adapter.client.shutdown.assert_called_once_with()

    def test_a_client_passed_in_is_left_open(self):
        client = make_client()

        LangfuseAdapter(client).close()

        client.shutdown.assert_not_called()


def _wait_for(read, done, timeout=120.0):
    """Poll `read()` until `done(result)`: Langfuse ingests in the background."""
    deadline = time.monotonic() + timeout
    while True:
        result = read()
        if done(result) or time.monotonic() > deadline:
            return result
        time.sleep(5)


@pytest.mark.skipif(
    not (os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY")),
    reason="needs LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY: exports to the real Langfuse",
)
def test_live_smoke():
    """Exports twice from two Adapters and reads back what Langfuse holds.

    Each assert answers a premise the in-memory fake cannot confirm: the dataset item is the
    Case, the OTLP spans are accepted with the right types, parents, usage and metadata, a
    re-export does not duplicate observations, each repetition is a dataset run, and trace-,
    observation- and run-level scores arrive. Set ASSAYER_SMOKE_KEEP=1 to keep the dataset for
    a look in the Langfuse UI.
    """
    name = f"assayer-smoke-{uuid.uuid4().hex[:8]}"
    case_id = f"{name}-c1"
    print(f"assayer smoke dataset: {name}")
    started = dt.datetime.now(dt.UTC)
    metric = Metric(name="exact", level="trajectory", fn=lambda t, c: 1.0)
    runner = Runner(_tool_then_model, [metric], repetitions=2)
    experiment = runner.run(Dataset(name, [Case(input="q", id=case_id, expected_output="answer")]))
    experiment.name = name
    experiment.scores.append(Score("overall", 0.5, target="experiment", field="f"))
    client = Langfuse()
    try:
        for _ in range(2):  # a new Adapter each time
            with LangfuseAdapter(client, started_at=started) as adapter:
                report = Runner(adapter=adapter).export(experiment)
            assert report.ok, report.failed
        window = started - dt.timedelta(minutes=5)

        item = client.api.dataset_items.get(case_id)
        assert item.id == case_id, "dataset item id must be the case_id"
        assert item.input == "q" and item.expected_output == "answer"

        traces = {trajectory_id(name, t.case_id, t.repetition) for t in experiment.trajectories}
        for trace_id in sorted(traces):
            observations = _wait_for(
                lambda trace_id=trace_id: (
                    client.api.observations.get_many(
                        trace_id=trace_id,
                        fields="core,basic,io,metadata,model,usage",
                        from_start_time=window,
                        limit=100,
                    ).data
                ),
                lambda found: len({o.id for o in found}) >= 5,
            )
            # Langfuse merges rows with the same id in the background, so a re-export can show
            # the same observation twice for a while; what matters is that no new id appears
            observations = list({o.id: o for o in observations}.values())
            assert len(observations) == 5, "root and four Steps, once each, after two exports"
            by_name = {o.name: o for o in observations}
            assert {o.type for o in observations} == {"SPAN", "RETRIEVER", "GENERATION", "TOOL"}
            assert by_name["search"].type == "RETRIEVER" and by_name["calc"].type == "TOOL"
            root = by_name[name]
            assert root.parent_observation_id is None
            assert by_name["search"].parent_observation_id == root.id
            assert by_name["gpt-x"].parent_observation_id == by_name["search"].id
            assert (by_name["gpt-x"].usage_details or {}).get("input") == 10
            assert (by_name["gpt-x"].usage_details or {}).get("output") == 5
            assert by_name["gpt-x"].model == "gpt-x"
            assert by_name["calc"].level == "ERROR"
            assert "answer" in str(root.metadata.get("final_output"))
            # Langfuse flattens JSON metadata into dotted keys
            assert root.metadata.get("final_state.done") is True
            assert root.session_id == "s1"

        runs = _wait_for(
            lambda: (
                client.api.experiments.list_items(
                    from_start_time=window, dataset_id=item.dataset_id
                ).data
            ),
            lambda found: len(found) >= 2,
        )
        assert sorted(r.experiment_name for r in runs) == [f"{name}/rep-0", f"{name}/rep-1"]
        assert {r.experiment_item_id for r in runs} == {case_id}

        def read_scores(name):
            return client.api.scores.get_many(
                name=name, from_timestamp=window, fields="details,subject"
            ).data

        def mine(read, owned):
            return lambda: [s for s in read() if (s.subject.kind, s.subject.id) in owned]

        owned = {("trace", t) for t in traces}
        scores = _wait_for(mine(lambda: read_scores("exact"), owned), lambda found: len(found) >= 2)
        assert {(s.subject.kind, s.subject.id) for s in scores} == owned
        assert all(s.data_type == "NUMERIC" and s.metadata["assayer.target"] for s in scores)
        owned = {("experiment", r.experiment_id) for r in runs}
        run_scores = _wait_for(
            mine(lambda: read_scores("overall.f"), owned), lambda found: len(found) >= 2
        )
        # the ids the adapter derived for the runs are the ones the server derived
        assert {(s.subject.kind, s.subject.id) for s in run_scores} == owned
    finally:
        if not os.environ.get("ASSAYER_SMOKE_KEEP"):
            try:
                client.api.dataset_items.delete(case_id)
            except ApiError:
                pass
