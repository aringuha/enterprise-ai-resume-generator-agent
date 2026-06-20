import logging
import sys
from app.core.config import settings

def configure_logging() -> None:
    logging.basicConfig(
        level=settings.log_level,
        stream=sys.stdout,
        format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
    )
