"""Example 6: Scoring live traffic, by logging it and scoring it in batches.

Assayer has no live mode of its own, but `Runner.score` evaluates outputs that were
collected beforehand, and that is all a live setup needs: capture each interaction
where your app serves it, then score the captured batch on a schedule (a cron job, a
worker, a notebook) or from a sample of the traffic.

Here the "app" is a function wrapped by `record`, which keeps what it served in a
list. Production traffic has no reference answer, so the metrics are reference-free:
a custom rule on the answer and a custom check on the cost per request.

Run:
    python examples/logged_traffic_scoring.py
"""

from assayer.metrics import Metric
from assayer.models import Case, Dataset, PricingConfig, Step, TokenUsage, Trajectory
from assayer.runner import Runner

logged: list[tuple[Case, Trajectory]] = []


def record(app):
    """Wrap the function that serves requests so each call is kept for later scoring."""

    def wrapped(request_id: str, text: str) -> str:
        answer, tokens_in, tokens_out = app(text)
        step = Step(
            kind="model",
            model="demo-model",
            usage=TokenUsage(input_tokens=tokens_in, output_tokens=tokens_out, cost_usd=None),
        )
        logged.append((Case(input=text, id=request_id), Trajectory([step], final_output=answer)))
        return answer

    return wrapped


@record
def app(text: str) -> tuple[str, int, int]:
    """The app being observed. In production this calls your model."""
    return ("I cannot help with that." if "password" in text else f"Sure: {text}"), 40, 12


def not_a_refusal(trajectory: Trajectory, case: Case) -> float:
    return float("cannot help" not in trajectory.final_output.lower())


def within_budget(trajectory: Trajectory, case: Case) -> float:
    return float(trajectory.total_usage().output_tokens <= 50)


metrics = [
    Metric("not_a_refusal", "trajectory", not_a_refusal),
    Metric("within_budget", "trajectory", within_budget),
]

# Traffic arrives...
for request_id, text in [("r1", "book a table"), ("r2", "what is my password"), ("r3", "say hi")]:
    app(request_id, text)


# ...and, every so often, a job scores what was captured since the last run.
def score_batch() -> None:
    batch, logged[:] = list(logged), []
    cases = [case for case, _ in batch]
    outputs = [trajectory for _, trajectory in batch]
    pricing = PricingConfig(cost_per_input_token=3e-6, cost_per_output_token=15e-6)
    experiment = Runner(metrics=metrics, pricing=pricing).score(Dataset("traffic", cases), outputs)

    cost = experiment.total_usage(pricing).cost_usd
    print(f"scored {len(experiment.trajectories)} requests, cost ${cost:.5f}")
    for score in experiment.scores:
        print(f"  {score.target_id or ''} {score.name:<14} {score.value:.0f}")


score_batch()
