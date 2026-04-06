from __future__ import annotations

import logging


def setup_logging(settings=None) -> None:
    level = logging.DEBUG if getattr(settings, "ENVIRONMENT", "development") == "development" else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
