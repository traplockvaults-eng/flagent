from typing import List, Tuple
from web3 import Web3
from agent.defi.abis import UNISWAP_V2_ROUTER_ABI

def v2_router(w3: Web3, address: str):
    return w3.eth.contract(address=Web3.to_checksum_address(address), abi=UNISWAP_V2_ROUTER_ABI)

def quote_v2_get_amounts_out(w3: Web3, router: str, amount_in: int, path: List[str]) -> List[int]:
    c = v2_router(w3, router)
    return c.functions.getAmountsOut(amount_in, path).call()

def encode_v2_swap_exact_tokens_for_tokens(
    w3: Web3,
    router: str,
    amount_in: int,
    amount_out_min: int,
    path: List[str],
    recipient: str,
    deadline: int
) -> bytes:
    c = v2_router(w3, router)
    return c.encode_abi(
        fn_name="swapExactTokensForTokens",
        args=[amount_in, amount_out_min, path, Web3.to_checksum_address(recipient), deadline],
    )
