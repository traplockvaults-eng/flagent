from typing import Tuple
from web3 import Web3

def estimate_dynamic_fees(w3: Web3, priority_gwei: float = 2.0) -> Tuple[int, int]:
    # Use feeHistory to suggest EIP-1559 fees
        try:
                history = w3.eth.fee_history(5, "latest", [10, 30, 50])
                        base = int(history["baseFeePerGas"][-1])
                            except Exception:
                                    base = w3.to_wei(15, "gwei")

                                        priority = w3.to_wei(priority_gwei, "gwei")
                                            max_fee = int(base + priority * 2)
                                                return max_fee, priority
        