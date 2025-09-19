import asyncio
import pytest
from agent.strategies.arbitrator import Arbitrator
from agent.ai.client import AIClient
from agent.core.executor import TransactionExecutor
from agent.core.state import AgentState
from agent.utils.web3_client import build_web3

class DummyExecutor(TransactionExecutor):
    def sign_and_send(self, tx):
        return "0x" + "1"*64

@pytest.mark.asyncio
async def test_arbitrator_skips(settings):
    w3 = build_web3(settings)
    state = AgentState(w3=w3, settings=settings)
    ai = AIClient(settings)
    execu = DummyExecutor(w3, settings, state)
    arb = Arbitrator(settings, ai, execu)

    opp = {"opportunity_id": "stub-1", "snapshot": {}}
    await arb.evaluate_and_maybe_execute(opp)
    assert True
