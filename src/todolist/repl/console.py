from rich.console import Console
from rich.theme import Theme

custom_theme = Theme({
    "info": "bold cyan",
    "warning": "bold yellow",
    "danger": "bold red",
    "success": "bold green"
})
console = Console(theme=custom_theme)