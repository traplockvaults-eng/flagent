from typing import Dict, Any
from web3 import Web3
from eth_account import Account
from agent.config import Settings
from agent.core.state import AgentState
from agent.utils.logger import get_logger

log = get_logger(__name__)

class TransactionExecutor:
    def __init__(self, w3: Web3, settings: Settings, state: AgentState):
            self.w3 = w3
                    self.settings = settings
                            self.state = state
                                    self._account = Account.from_key(settings.PRIVATE_KEY)

                                        def sign_and_send(self, tx: Dict[str, Any]) -> str:
                                                if self.settings.DRY_RUN:
                                                            log.info("tx.dry_run", tx=tx)
                                                                        return "0x" + "0" * 64

                                                                                stx = self._account.sign_transaction(tx)
                                                                                        tx_hash = self.w3.eth.send_raw_transaction(stx.rawTransaction)
                                                                                                log.info("tx.sent", tx_hash=tx_hash.hex())
                                                                                                        return tx_hash.hex()
                                                