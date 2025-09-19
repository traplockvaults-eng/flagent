from dataclasses import dataclass
from typing import List, Optional
from web3 import Web3
from agent.config import Settings
from agent.defi.uniswap_v2 import quote_v2_get_amounts_out
from agent.defi.uniswap_v3 import quote_v3_exact_input_single

@dataclass
class QuoteResult:
    amounts: List[int]
    gross_cycle_out: int
    premium: int
    gas_cost_wei: int
    expected_profit: int
    expected_net_profit: int

def estimate_gas_cost_wei(w3: Web3, settings: Settings, gas_limit: int = 350000) -> int:
    # Simple heuristic; refine with eth_estimateGas once end-to-end call path is in place
    max_fee, priority = w3.eth.max_priority_fee if hasattr(w3.eth, "max_priority_fee") else (0, 0)
    price = w3.to_wei(settings.GAS_PRIORITY_GWEI, "gwei") + w3.eth.gas_price
    return gas_limit * int(price)

def simulate_v2_cycle(
    w3: Web3,
    settings: Settings,
    router_a: str,
    router_b: str,
    token_in: str,
    mid_token: str,
    amount_in: int,
    gas_limit_hint: int = 350000
) -> QuoteResult:
    # WETH -> USDC on A, then USDC -> WETH on B
    amounts_a = quote_v2_get_amounts_out(w3, router_a, amount_in, [token_in, mid_token])
    out_mid = amounts_a[-1]
    amounts_b = quote_v2_get_amounts_out(w3, router_b, out_mid, [mid_token, token_in])
    out_back = amounts_b[-1]

    premium = (amount_in * settings.AAVE_PREMIUM_BPS) // 10_000
    gas_cost = estimate_gas_cost_wei(w3, settings, gas_limit_hint)

    expected_profit = out_back - amount_in
    expected_net = expected_profit - premium - gas_cost

    return QuoteResult(
        amounts=[amount_in, out_mid, out_back],
        gross_cycle_out=out_back,
        premium=premium,
        gas_cost_wei=gas_cost,
        expected_profit=expected_profit,
        expected_net_profit=expected_net,
    )

def simulate_v3_single(
    w3: Web3,
    settings: Settings,
    quoter: str,
    token_in: str,
    token_out: str,
    fee: int,
    amount_in: int,
    gas_limit_hint: int = 220000
) -> QuoteResult:
    out = quote_v3_exact_input_single(w3, quoter, token_in, token_out, fee, amount_in)
    premium = (amount_in * settings.AAVE_PREMIUM_BPS) // 10_000
    gas_cost = estimate_gas_cost_wei(w3, settings, gas_limit_hint)
    expected_profit = out - amount_in if token_out.lower() == token_in.lower() else 0
    expected_net = expected_profit - premium - gas_cost
    return QuoteResult(
        amounts=[amount_in, out],
        gross_cycle_out=out,
        premium=premium,
        gas_cost_wei=gas_cost,
        expected_profit=expected_profit,
        expected_net_profit=expected_net,
    )
