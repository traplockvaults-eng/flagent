import asyncio
from typing import AsyncGenerator, Dict, Any
from web3 import Web3
from agent.config import Settings
from agent.utils.logger import get_logger
from agent.utils.control import read_agent_enabled  # new
log = get_logger(__name__)
class OpportunityScanner:
    def __init__(self, w3: Web3, settings: Settings):
        self.w3 = w3
        self.settings = settings
async def scan_loop(self) -> AsyncGenerator[Dict[str, Any], None]:
    while True:
        # If disabled, sleep briefly and skip work
        if not read_agent_enabled(self.settings.AGENT_ENABLE_FILE):
            await asyncio.sleep(2.0)
            continue

        await asyncio.sleep(3)
        if False:
            yield {}