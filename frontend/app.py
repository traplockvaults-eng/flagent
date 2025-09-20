import json
import os
from typing import Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from web3 import Web3
PANEL_BIND = os.getenv("PANEL_BIND", "0.0.0.0")
PANEL_PORT = int(os.getenv("PANEL_PORT", "8000"))
AUTH_TOKEN = os.getenv("PANEL_AUTH_TOKEN", "")  # required for POST
EXECUTOR_ADDRESS = os.getenv("EXECUTOR_ADDRESS", "")
CHAIN_ID = int(os.getenv("CHAIN_ID", "1"))
AGENT_ENABLE_FILE = os.getenv("AGENT_ENABLE_FILE", "run/agent_enabled.flag")
# RPC selection (use your agent’s multi-rpc or fallback)
MULTI = [u.strip() for u in os.getenv("MULTI_RPC_HTTP_URLS", "").split(",") if u.strip()]
RPC_HTTP_URL = os.getenv("RPC_HTTP_URL", "").strip()
RPCS = MULTI if MULTI else ([RPC_HTTP_URL] if RPC_HTTP_URL else [])
FLASHBOTS_RELAY_URL = os.getenv("FLASHBOTS_RELAY_URL", "https://rpc.flashbots.net").strip()
USE_FLASHBOTS_FOR_ADMIN = os.getenv("USE_FLASHBOTS_FOR_ADMIN", "false").lower() in ("1", "true", "yes", "on")
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")
PUBLIC_ADDRESS = os.getenv("PUBLIC_ADDRESS", "")
app = FastAPI(title="Flashloan AI Agent Panel")
def get_best_w3() -> Web3:
    if not RPCS:
        raise RuntimeError("No RPC configured. Set MULTI_RPC_HTTP_URLS or RPC_HTTP_URL")
    best_url = RPCS[0]
    w3 = Web3(Web3.HTTPProvider(best_url, request_kwargs={"timeout": 20}))
    return w3
def get_sender_w3() -> Web3:
    if USE_FLASHBOTS_FOR_ADMIN:
        return Web3(Web3.HTTPProvider(FLASHBOTS_RELAY_URL, request_kwargs={"timeout": 20}))
    return get_best_w3()
def must_be_configured():
    if not EXECUTOR_ADDRESS or len(EXECUTOR_ADDRESS) != 42:
        raise HTTPException(500, "EXECUTOR_ADDRESS not configured")
    if not PRIVATE_KEY or not PUBLIC_ADDRESS:
        raise HTTPException(500, "Wallet PRIVATE_KEY/PUBLIC_ADDRESS not configured")
def load_executor_contract(w3: Web3):
    abi_path = os.path.join("abis", "AIFlashLoanExecutor.json")
    if not os.path.exists(abi_path):
        raise HTTPException(500, "Missing abis/AIFlashLoanExecutor.json; run forge build + export_abis")
    with open(abi_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    abi = data["abi"] if "abi" in data else data
    return w3.eth.contract(address=Web3.to_checksum_address(EXECUTOR_ADDRESS), abi=abi)
def assert_auth(request: Request):
    if not AUTH_TOKEN:
        raise HTTPException(401, "Panel not secured: set PANEL_AUTH_TOKEN")
    token = request.headers.get("Authorization", "")
    if not token.startswith("Bearer "):
        raise HTTPException(401, "Missing Bearer token")
    if token.split(" ", 1)[1] != AUTH_TOKEN:
        raise HTTPException(403, "Invalid token")
def read_agent_enabled(path: str) -> bool:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip() in ("1", "true", "yes", "on")
    except FileNotFoundError:
        return True
def write_agent_enabled(path: str, enabled: bool) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("1" if enabled else "0")
@app.get("/", response_class=HTMLResponse)
def index():
    w3 = get_best_w3()
    status = {
        "chain_id": CHAIN_ID,
        "block_number": w3.eth.block_number,
        "executor_address": EXECUTOR_ADDRESS or "(unset)",
        "agent_enabled": read_agent_enabled(AGENT_ENABLE_FILE),
        "owner": None,
        "paused": None,
        "public_address": PUBLIC_ADDRESS or "(unset)",
    }
    try:
        c = load_executor_contract(w3)
        status["owner"] = c.functions.owner().call()
        status["paused"] = c.functions.paused().call()
    except Exception:
        pass
    html = f"""
    <html>
      <head>
        <title>Flashloan Agent Panel</title>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 24px; }}
          .row {{ margin: 8px 0; }}
          button {{ padding: 8px 12px; margin-right: 8px; }}
          .warn {{ color: #b00; }}
          .ok {{ color: #070; }}
          code {{ background: #f3f3f3; padding: 2px 6px; }}
        </style>
        <script>
          async function postJson(url, body) {{
            const token = localStorage.getItem("panel_token") || "";
            const res = await fetch(url, {{
              method: "POST",
              headers: {{
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token
              }},
              body: JSON.stringify(body || {{}})
            }});
            const text = await res.text();
            alert(text);
            location.reload();
          }}
          function saveToken() {{
            const t = document.getElementById("token").value;
            localStorage.setItem("panel_token", t);
            alert("Token saved locally.");
          }}
        </script>
      </head>
      <body>
        <h2>Flashloan AI Agent - Access Panel</h2>
        <div class="row">Chain ID: <b>{status["chain_id"]}</b> | Block: <b>{status["block_number"]}</b></div>
        <div class="row">Executor: <code>{status["executor_address"]}</code></div>
        <div class="row">Owner: <code>{status["owner"]}</code></div>
        <div class="row">Paused: <b class="{ 'ok' if status['paused'] is False else 'warn' }">{status["paused"]}</b></div>
        <div class="row">Agent enabled: <b class="{ 'ok' if status['agent_enabled'] else 'warn' }">{status["agent_enabled"]}</b></div>
        <div class="row">Agent wallet: <code>{status["public_address"]}</code></div>

        <h3>Controls</h3>
        <div class="row">
          <input type="password" id="token" placeholder="PANEL_AUTH_TOKEN" />
          <button onclick="saveToken()">Save Token</button>
        </div>
        <div class="row">
          <button onclick="postJson('/api/agent/enable', {{enable:true}})">Enable Agent</button>
          <button onclick="postJson('/api/agent/enable', {{enable:false}})">Disable Agent</button>
        </div>
        <div class="row">
          <button onclick="postJson('/api/contract/pause', {{}})">Pause Contract</button>
          <button onclick="postJson('/api/contract/unpause', {{}})">Unpause Contract</button>
        </div>

        <p class="warn">Security: protect this panel with a VPN/reverse proxy. Do not expose publicly.</p>
      </body>
    </html>
    """
    return HTMLResponse(content=html)
@app.post("/api/agent/enable")
async def api_agent_enable(req: Request):
    assert_auth(req)
    body = await req.json()
    enabled = bool(body.get("enable", True))
    write_agent_enabled(AGENT_ENABLE_FILE, enabled)
    return PlainTextResponse("Agent " + ("enabled" if enabled else "disabled"))
def _sign_and_send(tx: dict) -> str:
    w3 = get_sender_w3()
    acct = w3.eth.account.from_key(PRIVATE_KEY)
    tx.setdefault("nonce", w3.eth.get_transaction_count(acct.address))
    tx.setdefault("chainId", CHAIN_ID)
    if "gas" not in tx:
        tx["gas"] = w3.eth.estimate_gas(tx)
    if "maxFeePerGas" not in tx or "maxPriorityFeePerGas" not in tx:
        # Simple EIP-1559
        base = w3.eth.gas_price
        tip = int(2e9)
        tx["maxPriorityFeePerGas"] = tip
        tx["maxFeePerGas"] = base + tip * 2
    stx = acct.sign_transaction(tx)
    txh = w3.eth.send_raw_transaction(stx.rawTransaction)
    return txh.hex()
@app.post("/api/contract/pause")
async def api_contract_pause(req: Request):
    assert_auth(req)
    must_be_configured()
    w3 = get_best_w3()
    c = load_executor_contract(w3)
    data = c.encode_abi(fn_name="pause", args=[])
    tx = {"to": c.address, "from": PUBLIC_ADDRESS, "data": data, "value": 0}
    txh = _sign_and_send(tx)
    return PlainTextResponse(f"Pause tx sent: {txh}")
@app.post("/api/contract/unpause")
async def api_contract_unpause(req: Request):
    assert_auth(req)
    must_be_configured()
    w3 = get_best_w3()
    c = load_executor_contract(w3)
    data = c.encode_abi(fn_name="unpause", args=[])
    tx = {"to": c.address, "from": PUBLIC_ADDRESS, "data": data, "value": 0}
    txh = _sign_and_send(tx)
    return PlainTextResponse(f"Unpause tx sent: {txh}")
# Run locally:
