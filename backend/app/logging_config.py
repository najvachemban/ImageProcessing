import logging
import sys


def setup_logging() -> None:import logging
import sys
import os


def setup_logging() -> None:
    os.makedirs("logs", exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),           # still prints to terminal
            logging.FileHandler("logs/app.log"),          # also writes to disk
        ],
    )
    """Configures root logging format/level for the whole application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )