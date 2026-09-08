"""Privacy-conscious logging configuration."""

import logging


def configure_logging(level: str = "INFO") -> None:
    """Configure application logs without document or query payloads."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        force=True,
    )

