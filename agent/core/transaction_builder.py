from typing import Dict, Any, Optional
from web3 import Web3
from agent.utils.gas_estimator import estimate_dynamic_fees
from agent.config import Settings

def build_transaction(
    w3: Web3,
        settings: Settings,
            tx: Dict[str, Any],
                nonce: Optional[int] = None,
                    max_gas_gwei: Optional[float] = None,
                    ) -> Dict[str, Any]:
                        chain_id = settings.CHAIN_ID
                            acct = settings.PUBLIC_ADDRESS

                                if nonce is None:
                                        nonce = w3.eth.get_transaction_count(acct)

                                            max_fee_per_gas, max_priority_fee_per_gas = estimate_dynamic_fees(
                                                    w3, priority_gwei=settings.GAS_PRIORITY_GWEI
                                                        )

                                                            if max_gas_gwei is not None:
                                                                    # Cap by AI decision
                                                                            max_fee_per_gas = min(max_fee_per_gas, int(max_gas_gwei * 1e9))

                                                                                tx_out = {
                                                                                        "chainId": chain_id,
                                                                                                "from": acct,
                                                                                                        "nonce": nonce,
                                                                                                                "to": tx.get("to"),
                                                                                                                        "data": tx.get("data", b""),
                                                                                                                                "value": tx.get("value", 0),
                                                                                                                                        "gas": tx.get("gas", 1_500_000),
                                                                                                                                                "maxFeePerGas": max_fee_per_gas,
                                                                                                                                                        "maxPriorityFeePerGas": max_priority_fee_per_gas,
                                                                                                                                                                "type": 2,
                                                                                                                                                                    }
                                                                                                                                                                        return tx_out
                                        