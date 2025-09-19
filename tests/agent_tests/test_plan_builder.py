from web3 import Web3
from agent.config import Settings
from agent.strategies.plan_builder import build_uniswap_v2_cycle_plan

def test_build_v2_plan_shape(monkeypatch):
    # Dummy w3 with no chain calls for this smoke test
    w3 = Web3(Web3.EthereumTesterProvider())
    settings = Settings(
        PRIVATE_KEY="0x"+"11"*32,
        PUBLIC_ADDRESS="0x0000000000000000000000000000000000000001",
        RPC_HTTP_URL="http://localhost:8545",
    )

    # Monkeypatch quotes to avoid network
    from agent.defi import uniswap_v2
    def fake_quote(w3, router, amount_in, path):
        if path[1].lower() == "0x0000000000000000000000000000000000000002":
            return [amount_in, amount_in * 2000]  # token_in -> mid
        else:
            return [amount_in * 2000, int(amount_in * 2000 * 999) // 1000]  # mid -> back with 0.1% fee
    monkeypatch.setattr(uniswap_v2, "quote_v2_get_amounts_out", fake_quote)

    params, info = build_uniswap_v2_cycle_plan(
        w3=w3,
        settings=settings,
        executor_address="0x0000000000000000000000000000000000000009",
        token_in="0x0000000000000000000000000000000000000001",
        mid_token="0x0000000000000000000000000000000000000002",
        router_a="0x00000000000000000000000000000000000000A1",
        router_b="0x00000000000000000000000000000000000000B1",
        amount_in=10**18,
    )
    assert isinstance(params, (bytes, bytearray))
    assert info["min_out_mid"] > 0
    assert info["min_out_back"] > 0
