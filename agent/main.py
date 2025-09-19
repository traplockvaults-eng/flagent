import asyncio
from agent.config import Settings
from agent.utils.logger import get_logger
from agent.utils.web3_client import build_web3
from agent.strategies.scanner import OpportunityScanner
from agent.strategies.arbitrator import Arbitrator
from agent.ai.client import AIClient
from agent.core.executor import TransactionExecutor
from agent.core.state import AgentState

log = get_logger(__name__)

async def main():
    settings = Settings()
    log.info("agent.start", version="0.1.0", chain_id=settings.CHAIN_ID, dry_run=settings.DRY_RUN)

    w3 = build_web3(settings)
    state = AgentState(w3=w3, settings=settings)

    ai_client = AIClient(settings=settings)
    executor = TransactionExecutor(w3=w3, settings=settings, state=state)

    scanner = OpportunityScanner(w3=w3, settings=settings)
    arbitrator = Arbitrator(w3=w3, settings=settings, ai_client=ai_client, executor=executor)

    async for opp in scanner.scan_loop():
        try:
            await arbitrator.evaluate_and_maybe_execute(opp)
        except Exception as e:
            log.exception("agent.error", msg=str(e))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("agent.exit")
