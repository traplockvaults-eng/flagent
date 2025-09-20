Flashloan AI Agent (Monorepo Scaffold)

Overview
- Python Agent that monitors markets, queries an AI for decision-making, and can assemble flash-loan arbitrage transactions.
- Solidity smart contracts (Foundry) for on-chain execution (stubbed).
- Docker stack to run agent + local testnet.

Warning
- This code is a scaffold for research and development. It is NOT production-ready.
- Flash loans and on-chain trading carry significant financial risk. Test on a fork or testnet only.

Quick Start
1) Prereqs:
   - Python 3.11+
   - Foundry (anvil, forge)
   - Docker (optional)
2) Install Python deps:
   - python -m venv .venv && source .venv/bin/activate
   - pip install -r requirements.txt
3) Configure environment:
   - cp .env .env.local and edit values
4) Run local anvil:
   - anvil
5) Run agent:
   - source .venv/bin/activate
   - export $(grep -v '^#' .env.local | xargs) || true
   - python -m agent.main

Foundry
- forge build
- forge test

Docker
- docker-compose up --build

Structure
- agent/: Python app (AI, scanning, tx assembly).
- contracts/: Solidity sources.
- abis/: Placeholder ABIs (replace with compiled outputs).
- tests/: Python tests for agent, Forge tests for contracts.

Notes
- AI calls are stubbed by default; see agent/ai/client.py.
- Fill prompts under agent/ai/prompts.
- Implement real flash-loan and DEX integrations before using on mainnet.

Flash Loan (Aave V3) Contract
- Contract implements Aave V3 IFlashLoanSimpleReceiver with guardrails (Ownable, Pausable, ReentrancyGuard, allowlists).
- Params encoding: use agent/core/flash_params.py encode_flash_params().

Foundry Fork Test
- Requires a mainnet RPC URL with archive or recent state:
  export MAINNET_RPC_URL=https://mainnet.infura.io/v3/YOUR_KEY
- Run:
  forge test -vvv --match-test testFlashLoanSimple_WETH_NoOps_MinProfitZero

ABI Export
- Local:
  forge build
  bash scripts/export_abis.sh
- CI automatically builds and publishes ABIs as an artifact.

Python Usage
- Build and export ABIs, then in Python:
  from json import load
  from web3 import Web3
  from agent.core.flash_params import encode_flash_params

  w3 = Web3(Web3.HTTPProvider(RPC_HTTP_URL))
  with open('abis/AIFlashLoanExecutor.json') as f:
      abi = load(f)['abi']
  executor = w3.eth.contract(address=EXECUTOR_ADDRESS, abi=abi)
  params = encode_flash_params(
      min_profit=0,
      beneficiary="0x0000000000000000000000000000000000000000",
      approvals=[],
      calls=[]
  )
  tx = executor.functions.executeFlashLoan(WETH_ADDRESS, 10**18, bytes(params)).build_transaction({...})
