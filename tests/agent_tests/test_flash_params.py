from agent.core.flash_params import encode_flash_params

def test_encode_flash_params_roundtrip_smoke():
    params = encode_flash_params(
        min_profit=0,
        beneficiary="0x0000000000000000000000000000000000000000",
        approvals=[],
        calls=[
            {
                "target": "0x0000000000000000000000000000000000000001",
                "value": 0,
                "data": "0x",
            }
        ],
    )
    assert isinstance(params, (bytes, bytearray))
    assert len(params) > 0
