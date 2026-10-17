from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage

from assayer.judges import Judge, LangChainJudge, call_judge, track_judge


class UsageModel:
    def __init__(self, reply):
        self.reply = reply
        self.seen = None

    def invoke(self, messages):
        self.seen = messages
        return self.reply


def test_is_a_judge():
    assert isinstance(LangChainJudge(FakeListChatModel(responses=["x"])), Judge)


def test_returns_the_reply_text():
    judge = LangChainJudge(FakeListChatModel(responses=["score: 1"]))
    response = judge.complete([{"role": "user", "content": "hi"}])
    assert response.text == "score: 1"
    assert response.usage is None


def test_sends_messages_with_their_roles():
    model = UsageModel(AIMessage(content="ok"))
    LangChainJudge(model).complete(
        [{"role": "system", "content": "be strict"}, {"role": "user", "content": "grade"}]
    )
    assert model.seen == [("system", "be strict"), ("user", "grade")]


def test_reads_usage_metadata():
    reply = AIMessage(
        content="ok",
        usage_metadata={"input_tokens": 3, "output_tokens": 5, "total_tokens": 8},
    )
    response = LangChainJudge(UsageModel(reply)).complete([{"role": "user", "content": "q"}])
    assert (response.usage.input_tokens, response.usage.output_tokens) == (3, 5)
    assert response.usage.cost_usd is None


def test_joins_text_blocks():
    reply = AIMessage(content=[{"type": "text", "text": "a"}, {"type": "image", "x": 1}, "b"])
    response = LangChainJudge(UsageModel(reply)).complete([{"role": "user", "content": "q"}])
    assert response.text == "ab"


def test_works_injected_through_the_ledger():
    judge = LangChainJudge(FakeListChatModel(responses=["fine"]))
    with track_judge() as ledger:
        call_judge(judge, [{"role": "user", "content": "q"}])
    assert ledger.calls == 1
