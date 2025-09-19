from agent.ai.client import AIClient
from agent.config import Settings

def test_ai_client_stubs(settings: Settings):
    client = AIClient(settings=settings)
    analysis = client.analyze_arbitrage({"markets": []})
    assert analysis.opportunity_id == "stub-1"

    risk = client.assess_risk(analysis.model_dump())
    assert risk.opportunity_id == "stub-1"
    assert isinstance(risk.risk_score, float)

    decision = client.decide_execution(risk.model_dump())
    assert decision.opportunity_id == "stub-1"
    assert decision.execute is False
