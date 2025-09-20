from typing import Dict, Any, Optional, Tuple
from web3 import Web3
from agent.config import Settings
from agent.ai.client import AIClient
from agent.ai.parser import ArbAnalysis
from agent.core.transaction_builder import build_transaction
from agent.core.executor import TransactionExecutor
from agent.utils.logger import get_logger
from agent.strategies.plan_builder import build_uniswap_v2_cycle_plan
from agent.strategies.simulator import simulate_v2_cycle

import json
import os

log = get_logger(__name__)

DEX_NAME_MAP = {
    "uniswapv2": "uniswapv2",
    "uniswap v2": "uniswapv2",
    "uniswap": "uniswapv2",
    "sushiswap": "sushiswap",
    "sushi": "sushiswap",
}

class Arbitrator:
    def __init__(self, w3: Web3, settings: Settings, ai_client: AIClient, executor: TransactionExecutor):
        self.w3 = w3
        self.settings = settings
        self.ai = ai_client
        self.executor = executor
        self._executor_contract = self._load_executor_contract()

    def _load_executor_contract(self):
        if not self.settings.EXECUTOR_ADDRESS:
            raise ValueError("EXECUTOR_ADDRESS is not configured in Settings")
        abi_path = os.path.join("abis", "AIFlashLoanExecutor.json")
        if not os.path.exists(abi_path):
            raise FileNotFoundError("Missing abis/AIFlashLoanExecutor.json. Run forge build + scripts/export_abis.sh")
        with open(abi_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            abi = data["abi"] if "abi" in data else data
        return self.w3.eth.contract(address=Web3.to_checksum_address(self.settings.EXECUTOR_ADDRESS), abi=abi)

    def _normalize_dex_name(self, name: str) -> Optional[str]:
        key = (name or "").strip().lower()
        return DEX_NAME_MAP.get(key)

    def _router_address_for(self, dex_name: str) -> Optional[str]:
        n = self._normalize_dex_name(dex_name)
        if n == "uniswapv2":
            return self.settings.UNISWAP_V2_ROUTER
        if n == "sushiswap":
            return self.settings.SUSHISWAP_V2_ROUTER
        return None

    def _looks_like_address(self, s: str) -> bool:
        return isinstance(s, str) and s.startswith("0x") and len(s) == 42

    def _select_v2_cycle(self, analysis: ArbAnalysis) -> Optional[Tuple[str, str, str, str]]:
        """
        Returns (token_in, mid_token, router_a, router_b) if a compatible V2 cycle path is found.
        Expects analysis.paths[*] with:
          - dex_sequence length 2, recognizable as UniswapV2/Sushiswap
          - assets length 2 or 3. Prefer [token_in, mid_token, token_in] or [token_in, mid_token].
          - assets must be addresses.
        """
        for p in analysis.paths:
            if not p.dex_sequence or len(p.dex_sequence) != 2:
                continue
            r_a = self._router_address_for(p.dex_sequence[0])
            r_b = self._router_address_for(p.dex_sequence[1])
            if not r_a or not r_b:
                continue

            if not p.assets or len(p.assets) < 2:
                continue
            a0 = p.assets[0]
            a1 = p.assets[1]
            if not (self._looks_like_address(a0) and self._looks_like_address(a1)):
                continue

            # If 3 assets provided and the 3rd equals the first, it's a full cycle hint.
            if len(p.assets) >= 3 and self._looks_like_address(p.assets[2]) and p.assets[2].lower() == a0.lower():
                return (a0, a1, r_a, r_b)

            # Otherwise, assume cycle back using the second hop path; we'll enforce minOut on final hop.
            return (a0, a1, r_a, r_b)
        return None

    async def evaluate_and_maybe_execute(self, opp: Dict[str, Any]) -> None:
        opp_id = opp.get("opportunity_id", "unknown")
        snapshot = opp.get("snapshot", opp)

        analysis = self.ai.analyze_arbitrage(snapshot)
        log.info("ai.analysis", opportunity_id=analysis.opportunity_id, confidence=analysis.confidence)

        # Attempt to find a Uniswap V2 two-hop cycle plan candidate from the analysis
        candidate = self._select_v2_cycle(analysis)
        if not candidate:
            log.info("arb.no_supported_path", opportunity_id=opp_id)
            return

        token_in, mid_token, router_a, router_b = candidate

        # Amount: prefer AI suggested amounts[0] if looks like int, else fallback to settings
        amount_in = None
        try:
            if analysis.paths and analysis.paths[0].amounts:
                # Accept string/integer; assume wei
                amount_in = int(analysis.paths[0].amounts[0])
        except Exception:
            amount_in = None
        if not amount_in or amount_in <= 0:
            amount_in = int(self.settings.DEFAULT_FLASHLOAN_AMOUNT_WEI)

        # Simulate the cycle using quotes to ensure expected net profitability
        sim = simulate_v2_cycle(
            w3=self.w3,
            settings=self.settings,
            router_a=router_a,
            router_b=router_b,
            token_in=token_in,
            mid_token=mid_token,
            amount_in=amount_in,
            gas_limit_hint=1_000_000,
        )
        log.info(
            "arb.simulation",
            opportunity_id=opp_id,
            gross_out=sim.gross_cycle_out,
            premium=sim.premium,
            gas_cost_wei=sim.gas_cost_wei,
            expected_profit=sim.expected_profit,
            expected_net_profit=sim.expected_net_profit,
        )

        # Ask AI for risk and decision after we have a concrete plan sketch
        risk = self.ai.assess_risk(analysis.model_dump())
        log.info("ai.risk", opportunity_id=risk.opportunity_id, score=risk.risk_score, recommendation=risk.recommendation)

        decision = self.ai.decide_execution(risk.model_dump())
        log.info("ai.decision", opportunity_id=decision.opportunity_id, execute=decision.execute, reason=decision.reason)

        # Hard backstop: require positive expected net profit from deterministic sim
        if not decision.execute or sim.expected_net_profit <= 0:
            log.info("arb.skip", opportunity_id=opp_id, reason="unprofitable_or_ai_declined")
            return

        # Build the on-chain plan params with minOut backstops
        params, info = build_uniswap_v2_cycle_plan(
            w3=self.w3,
            settings=self.settings,
            executor_address=self.settings.EXECUTOR_ADDRESS,
            token_in=token_in,
            mid_token=mid_token,
            router_a=router_a,
            router_b=router_b,
            amount_in=amount_in,
        )
        log.info("arb.plan", opportunity_id=opp_id, info=info)

        # Encode function call to executor
        data = self._executor_contract.encode_abi(
            fn_name="executeFlashLoan",
            args=[Web3.to_checksum_address(token_in), int(amount_in), bytes(params)],
        )

        # Build and submit transaction
        tx_template = {
            "to": Web3.to_checksum_address(self.settings.EXECUTOR_ADDRESS),
            "data": data,
            "value": 0,
            "gas": 1_000_000,
        }
        tx = build_transaction(
            w3=self.executor.w3,
            settings=self.settings,
            tx=tx_template,
            max_gas_gwei=decision.max_gas_gwei,
        )
        tx_hash = self.executor.sign_and_send(tx)
        log.info("arb.executed", opportunity_id=opp_id, tx_hash=tx_hash)
