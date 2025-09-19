from __future__ import annotations

from typing import Iterable, Mapping, Any, List, Tuple
from hexbytes import HexBytes
from eth_abi import encode as abi_encode


def _to_bytes(data: Any) -> bytes:
    if data is None:
            return b""
                if isinstance(data, bytes):
                        return data
                            if isinstance(data, bytearray):
                                    return bytes(data)
                                        if isinstance(data, str):
                                                s = data
                                                        if s.startswith("0x") or s.startswith("0X"):
                                                                    return bytes.fromhex(s[2:])
                                                                            # treat as utf-8 if not hex
                                                                                    return s.encode("utf-8")
                                                                                        raise TypeError(f"Unsupported bytes-like type: {type(data)}")


                                                                                        def encode_flash_params(
                                                                                            *,
                                                                                                min_profit: int,
                                                                                                    beneficiary: str,
                                                                                                        approvals: Iterable[Mapping[str, Any]] | None = None,
                                                                                                            calls: Iterable[Mapping[str, Any]] | None = None,
                                                                                                            ) -> HexBytes:
                                                                                                                """
                                                                                                                    Encodes AIFlashLoanExecutor.FlashParams to ABI-encoded bytes.

                                                                                                                        FlashParams solidity layout:
                                                                                                                            tuple(
                                                                                                                                  uint256 minProfit,
                                                                                                                                        address beneficiary,
                                                                                                                                              tuple(address token, address spender, uint256 amount)[] approvals,
                                                                                                                                                    tuple(address target, uint256 value, bytes data)[] calls
                                                                                                                                                        )
                                                                                                                                                            """
                                                                                                                                                                approvals_list: List[Tuple[str, str, int]] = []
                                                                                                                                                                    for a in (approvals or []):
                                                                                                                                                                            approvals_list.append(
                                                                                                                                                                                        (a["token"], a["spender"], int(a["amount"]))
                                                                                                                                                                                                )

                                                                                                                                                                                                    calls_list: List[Tuple[str, int, bytes]] = []
                                                                                                                                                                                                        for c in (calls or []):
                                                                                                                                                                                                                calls_list.append(
                                                                                                                                                                                                                            (
                                                                                                                                                                                                                                            c["target"],
                                                                                                                                                                                                                                                            int(c.get("value", 0)),
                                                                                                                                                                                                                                                                            _to_bytes(c.get("data", b"")),
                                                                                                                                                                                                                                                                                        )
                                                                                                                                                                                                                                                                                                )

                                                                                                                                                                                                                                                                                                    types = ["(uint256,address,(address,address,uint256)[],(address,uint256,bytes)[])"]
                                                                                                                                                                                                                                                                                                        values = [(int(min_profit), beneficiary, approvals_list, calls_list)]
                                                                                                                                                                                                                                                                                                            return HexBytes(abi_encode(types, values))
                                                                                                                                                                            