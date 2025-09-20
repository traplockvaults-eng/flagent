from __future__ import annotations
import os
def read_agent_enabled(path: str) -> bool:
	try:
		with open(path, "r", encoding="utf-8") as f:
			v = f.read().strip().lower()
			return v in ("1", "true", "yes", "on")
	except FileNotFoundError:
		# If flag is absent, default to enabled
		return True
def write_agent_enabled(path: str, enabled: bool) -> None:
	os.makedirs(os.path.dirname(path), exist_ok=True)
	with open(path, "w", encoding="utf-8") as f:
		f.write("1" if enabled else "0")