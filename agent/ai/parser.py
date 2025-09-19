import json
from pydantic import BaseModel, Field, ValidationError
from typing import List, Any, Dict

class ArbPath(BaseModel):
    dex_sequence: List[str] = Field(default_factory=list)
        assets: List[str] = Field(default_factory=list)
            amounts: List[str] = Field(default_factory=list)
                expected_profit_usd: float = 0.0

                class ArbAnalysis(BaseModel):
                    opportunity_id: str
                        paths: List[ArbPath] = Field(default_factory=list)
                            confidence: float = 0.0

                            class RiskAssessment(BaseModel):
                                opportunity_id: str
                                    risk_score: float
                                        risks: List[str] = Field(default_factory=list)
                                            recommendation: str

                                            class ExecutionDecision(BaseModel):
                                                opportunity_id: str
                                                    execute: bool
                                                        reason: str = ""
                                                            max_gas_gwei: float | None = None

                                                            def _parse_json(raw: str) -> Dict[str, Any]:
                                                                try:
                                                                        return json.loads(raw)
                                                                            except Exception as e:
                                                                                    raise ValueError(f"AI returned invalid JSON: {e}")

                                                                                    def parse_arb_analysis(raw: str) -> ArbAnalysis:
                                                                                        data = _parse_json(raw)
                                                                                            try:
                                                                                                    return ArbAnalysis(**data)
                                                                                                        except ValidationError as e:
                                                                                                                raise ValueError(f"Invalid ArbAnalysis schema: {e}")

                                                                                                                def parse_risk_assessment(raw: str) -> RiskAssessment:
                                                                                                                    data = _parse_json(raw)
                                                                                                                        try:
                                                                                                                                return RiskAssessment(**data)
                                                                                                                                    except ValidationError as e:
                                                                                                                                            raise ValueError(f"Invalid RiskAssessment schema: {e}")

                                                                                                                                            def parse_execution_decision(raw: str) -> ExecutionDecision:
                                                                                                                                                data = _parse_json(raw)
                                                                                                                                                    try:
                                                                                                                                                            return ExecutionDecision(**data)
                                                                                                                                                                except ValidationError as e:
                                                                                                                                                                        raise ValueError(f"Invalid ExecutionDecision schema: {e}")
                                                                                                                                                