import time
from typing import Dict, Any, List, Tuple
from web3 import Web3
from agent.config import Settings
from agent.core.flash_params import encode_flash_params
from agent.defi.uniswap_v2 import encode_v2_swap_exact_tokens_for_tokens, quote_v2_get_amounts_out
from agent.defi.uniswap_v3 import encode_v3_exact_input_single, quote_v3_exact_input_single

def _slip(value: int, slippage_bps: int) -> int:
    return (value * (10_000 - slippage_bps)) // 10_000

def build_uniswap_v2_cycle_plan(
    w3: Web3,
    settings: Settings,
    executor_address: str,
    token_in: str,
    mid_token: str,
    router_a: str,
    router_b: str,
    amount_in: int,
    slippage_bps: int | None = None,
) -> Tuple[bytes, Dict[str, Any]]:
    # Quote
    amounts_a = quote_v2_get_amounts_out(w3, router_a, amount_in, [token_in, mid_token])
    out_mid = amounts_a[-1]
    amounts_b = quote_v2_get_amounts_out(w3, router_b, out_mid, [mid_token, token_in])
    out_back = amounts_b[-1]

    slip_bps = slippage_bps if slippage_bps is not None else settings.DEFAULT_SLIPPAGE_BPS
    min_out_mid = _slip(out_mid, slip_bps)
    min_out_back = _slip(out_back, slip_bps)

    deadline = int(time.time()) + 600
    exec_addr = Web3.to_checksum_address(executor_address)

    call1_data = encode_v2_swap_exact_tokens_for_tokens(
        w3, router_a, amount_in, min_out_mid, [token_in, mid_token], exec_addr, deadline
    )
    call2_data = encode_v2_swap_exact_tokens_for_tokens(
        w3, router_b, out_mid, min_out_back, [mid_token, token_in], exec_addr, deadline
    )

    approvals = [
        {"token": token_in, "spender": router_a, "amount": amount_in},
        {"token": mid_token, "spender": router_b, "amount": out_mid},
    ]
    calls = [
        {"target": router_a, "value": 0, "data": call1_data},
        {"target": router_b, "value": 0, "data": call2_data},
    ]

    premium = (amount_in * settings.AAVE_PREMIUM_BPS) // 10_000
    expected_profit = out_back - amount_in
    # Very conservative minProfit; can be tuned. Ensure non-negative.
    min_profit = max(expected_profit - premium, 0)

    params = encode_flash_params(
        min_profit=int(min_profit),
        beneficiary=settings.PUBLIC_ADDRESS,
        approvals=approvals,
        calls=calls,
    )

    info = {
        "quotes": {"out_mid": int(out_mid), "out_back": int(out_back)},
        "slippage_bps": slip_bps,
        "min_out_mid": int(min_out_mid),
        "min_out_back": int(min_out_back),
        "expected_profit": int(expected_profit),
        "premium": int(premium),
        "min_profit": int(min_profit),
    }
    return bytes(params), info

def build_uniswap_v3_exact_input_single_plan(
    w3: Web3,
    settings: Settings,
    executor_address: str,
    token_in: str,
    token_out: str,
    fee: int,
    router_v3: str,
    quoter_v3: str,
    amount_in: int,
    slippage_bps: int | None = None,
) -> Tuple[bytes, Dict[str, Any]]:
    out = quote_v3_exact_input_single(w3, quoter_v3, token_in, token_out, fee, amount_in)
    slip_bps = slippage_bps if slippage_bps is not None else settings.DEFAULT_SLIPPAGE_BPS
    min_out = _slip(out, slip_bps)
    deadline = int(time.time()) + 600
    exec_addr = Web3.to_checksum_address(executor_address)

    call_data = encode_v3_exact_input_single(
        w3, router_v3, token_in, token_out, fee, exec_addr, deadline, amount_in, min_out
    )

    approvals = [{"token": token_in, "spender": router_v3, "amount": amount_in}]
    calls = [{"target": router_v3, "value": 0, "data": call_data}]

    premium = (amount_in * settings.AAVE_PREMIUM_BPS) // 10_000
    # If not a cycle back to token_in, expected_profit here is informational only
    expected_profit = 0
    min_profit = 0

    params = encode_flash_params(
        min_profit=min_profit,
        beneficiary=settings.PUBLIC_ADDRESS,
        approvals=approvals,
        calls=calls,
    )

    info = {
        "quote_out": int(out),
        "slippage_bps": slip_bps,
        "min_out": int(min_out),
        "premium": int(premium),
    }
    return bytes(params), info
