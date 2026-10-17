from assayer.adapters import AdapterCallError, plan_export, run_export
from assayer.models import Case, Dataset
from assayer.runner import Runner


def _plan():
    experiment = Runner(lambda v: v).run(Dataset("d", [Case(input="a", id="c1")]))
    return plan_export(experiment)


def test_plan_lists_cases_then_trajectories_with_their_steps():
    plan = _plan()

    assert [p.item.target_kind for p in plan.items] == ["case", "trajectory", "step"]
    assert plan.notes == []


def test_auth_failure_skips_every_item_after_it():
    plan = _plan()

    def send(entry):
        if entry.item.target_kind == "trajectory":
            raise AdapterCallError("auth", "no")

    report = run_export(plan, send)

    assert [i.target_kind for i in report.confirmed] == ["case"]
    assert [f.kind for f in report.failed] == ["auth"]
    assert [i.target_kind for i in report.skipped] == ["step"]


def test_an_unexpected_exception_becomes_an_unknown_failure():
    def send(entry):
        raise RuntimeError("boom")

    report = run_export(_plan(), send)

    assert {f.kind for f in report.failed} == {"unknown"}
    assert report.failed[0].message == "RuntimeError: boom"
