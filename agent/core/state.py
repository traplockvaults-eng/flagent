from dataclasses import dataclass, field
from typing import Dict, Any
from web3 import Web3
from agent.config import Settings

@dataclass
class AgentState:
    w3: Web3
        settings: Settings
            metadata: Dict[str, Any] = field(default_factory=dict)
    