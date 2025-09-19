from web3 import Web3
from web3.middleware import geth_poa_middleware
from agent.config import Settings

def build_web3(settings: Settings) -> Web3:
    w3 = Web3(Web3.HTTPProvider(settings.RPC_HTTP_URL, request_kwargs={"timeout": 30}))
        if settings.CHAIN_ID in (5, 10, 56, 100, 137, 250, 42161, 43114, 8453, 1101):
                # Some chains need POA middleware
                        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                            return w3
    