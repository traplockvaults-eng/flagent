import os
import structlog
from agent.config import Settings

def _level_from_env(default="INFO"):
    return os.getenv("LOG_LEVEL", default)

    def get_logger(name: str):
        structlog.configure(
                processors=[
                            structlog.processors.add_log_level,
                                        structlog.processors.TimeStamper(fmt="ISO"),
                                                    structlog.processors.JSONRenderer(),
                                                            ]
                                                                )
                                                                    return structlog.get_logger(name)
    