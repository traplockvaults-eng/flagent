from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # AI
    AI_PROVIDER: str = Field(default="openai")
    AI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20240620"

    # Chain
    CHAIN_ID: int = 1
    RPC_HTTP_URL: str
    RPC_WS_URL: str | None = None

    # Wallet
    PRIVATE_KEY: str
    PUBLIC_ADDRESS: str

    # Behavior
    DRY_RUN: bool = True
    MEV_PROTECT: bool = False
    FLASHBOTS_RELAY_URL: str | None = None

    # Gas
    GAS_PRIORITY_GWEI: float = 2.0
    MAX_FEE_MULTIPLIER: float = 1.2

    # Trading/backstops
    # Approximate Aave V3 simple flash-loan premium (in basis points)
    AAVE_PREMIUM_BPS: int = 5
    # Default slippage for DEX minOut (in basis points)
    DEFAULT_SLIPPAGE_BPS: int = 50
    # Default flash-loan amount in wei used when AI doesn't supply one
    DEFAULT_FLASHLOAN_AMOUNT_WEI: int = 10**18

    # Contracts and addresses
    # AIFlashLoanExecutor deployed address (must be set before executing)
    EXECUTOR_ADDRESS: str = Field(default="")
    # Aave V3 PoolAddressesProvider (mainnet default)
    AAVE_V3_ADDRESSES_PROVIDER: str = "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb"
    # DEX Routers (mainnet defaults)
    UNISWAP_V2_ROUTER: str = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
    SUSHISWAP_V2_ROUTER: str = "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F"

    # Logging
    LOG_LEVEL: str = "INFO"
