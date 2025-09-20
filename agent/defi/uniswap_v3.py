from web3 import Web3
from agent.defi.abis import UNISWAP_V3_QUOTER_ABI, UNISWAP_V3_SWAP_ROUTER_ABI

def v3_quoter(w3: Web3, address: str):
    return w3.eth.contract(address=Web3.to_checksum_address(address), abi=UNISWAP_V3_QUOTER_ABI)

def v3_swap_router(w3: Web3, address: str):
    return w3.eth.contract(address=Web3.to_checksum_address(address), abi=UNISWAP_V3_SWAP_ROUTER_ABI)

def quote_v3_exact_input_single(
    w3: Web3, quoter: str, token_in: str, token_out: str, fee: int, amount_in: int
) -> int:
    c = v3_quoter(w3, quoter)
    return c.functions.quoteExactInputSingle(
        Web3.to_checksum_address(token_in),
        Web3.to_checksum_address(token_out),
        fee,
        amount_in,
        0
    ).call()

def encode_v3_exact_input_single(
    w3: Web3,
    router: str,
    token_in: str,
    token_out: str,
    fee: int,
    recipient: str,
    deadline: int,
    amount_in: int,
    amount_out_min: int,
    sqrt_price_limit_x96: int = 0
) -> bytes:
    c = v3_swap_router(w3, router)
    params = (
        Web3.to_checksum_address(token_in),
        Web3.to_checksum_address(token_out),
        int(fee),
        Web3.to_checksum_address(recipient),
        int(deadline),
        int(amount_in),
        int(amount_out_min),
        int(sqrt_price_limit_x96),
    )
    # exactInputSingle((address,address,uint24,address,uint256,uint256,uint256,uint160))
    return c.encode_abi(fn_name="exactInputSingle", args=[params])
