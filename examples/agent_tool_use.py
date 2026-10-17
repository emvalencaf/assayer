"""Example 5: An agent scored on the tools it called, the state it left and its cost.

Scenario: A support agent must look an order up and, if it is late, refund it. It
reports what it did as a `Trajectory`: model Steps with their tokens, tool Steps with
their arguments, a final answer and the state of the system afterwards.

We use:
- the agent metrics: `tool_correctness`, `tool_argument_match`, `end_state_match`
  and `step_efficiency`;
- `PricingConfig` and `compare` to put two agents side by side, on quality and cost.

Run:
    python examples/agent_tool_use.py
"""

from assayer.metrics import register_agent_metrics
from assayer.models import Case, Dataset, PricingConfig, Step, TokenUsage, Trajectory
from assayer.registries import Registry
from assayer.runner import Runner, compare

registry = Registry()
register_agent_metrics(registry)
metrics = [
    registry.get(name)
    for name in ("tool_correctness", "tool_argument_match", "end_state_match", "step_efficiency")
]


def model(step_id: str, tokens_in: int, tokens_out: int) -> Step:
    return Step(
        kind="model",
        id=step_id,
        model="demo-model",
        usage=TokenUsage(input_tokens=tokens_in, output_tokens=tokens_out, cost_usd=None),
    )


def careful_agent(request: str) -> Trajectory:
    """Look the order up, refund it, then answer. In production this is your agent loop."""
    return Trajectory(
        steps=[
            model("m1", 120, 30),
            Step(kind="tool", id="t1", name="get_order", input={"order_id": "A-7"}),
            model("m2", 200, 40),
            Step(kind="tool", id="t2", name="refund", input={"order_id": "A-7", "amount": 30}),
            model("m3", 260, 50),
        ],
        final_output="Your order A-7 was refunded.",
        final_state={"orders": {"A-7": {"status": "refunded"}}},
    )


def hasty_agent(request: str) -> Trajectory:
    """Refunds without looking the order up, and with the wrong amount."""
    return Trajectory(
        steps=[
            model("m1", 120, 30),
            Step(kind="tool", id="t1", name="refund", input={"order_id": "A-7", "amount": 3}),
            model("m2", 150, 40),
        ],
        final_output="Done.",
        final_state={"orders": {"A-7": {"status": "refunded"}}},
    )


dataset = Dataset(
    "refund-agent",
    [
        Case(
            input="My order A-7 is late, I want my money back",
            id="late-order",
            expected_tool_calls=[
                {"name": "get_order", "arguments": {"order_id": "A-7"}},
                {"name": "refund", "arguments": {"order_id": "A-7", "amount": 30}},
            ],
            expected_steps=["model", "tool", "model", "tool", "model"],
            expected_state={"orders": {"A-7": {"status": "refunded"}}},
        )
    ],
)

pricing = PricingConfig(cost_per_input_token=3e-6, cost_per_output_token=15e-6)
careful = Runner(careful_agent, metrics, pricing=pricing).run(dataset)
hasty = Runner(hasty_agent, metrics, pricing=pricing).run(dataset)

for label, experiment in (("careful", careful), ("hasty", hasty)):
    print(f"=== {label} ===")
    for score in experiment.scores:
        if score.field is None and score.target == "trajectory":
            print(f"  {score.name:<20} {score.value:.2f}")
    print(f"  cost                 ${experiment.total_usage(pricing).cost_usd:.5f}\n")

delta = compare(careful, hasty)
print("hasty minus careful:")
for (name, _), value in delta.metric_deltas.items():
    if value is not None and value != 0:
        print(f"  {name:<20} {value:+.2f}")
print(f"  cost per Case        {delta.cost_usd_delta:+.5f} USD")
