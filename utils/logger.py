"""
📋 Custom logger (success, error, debug)
"""

import logging
from rich.logging import RichHandler
from rich.console import Console

# -----------------
# LOGGER SETUP
# -----------------

logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

log = logging.getLogger("rich")
console = Console()

# -----------------
# CUSTOM LOG FUNCTIONS
# -----------------

def log_success(message):
    console.print(f"[bold green]SUCCESS:[/] {message}")

def log_error(message):
    console.print(f"[bold red]ERROR:[/] {message}")

def log_debug(message):
    console.print(f"[bold yellow]DEBUG:[/] {message}")

def log_info(message):
    console.print(f"[bold blue]INFO:[/] {message}")
