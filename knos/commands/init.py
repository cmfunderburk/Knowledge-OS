"""Initialize KnOS configuration."""
from pathlib import Path
import shutil

from rich.console import Console
from rich.prompt import Prompt
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = REPO_ROOT / "config"


def run_init(force: bool = False) -> None:
    """Copy example configs and prompt for API key."""
    console = Console()

    CONFIG_DIR.mkdir(exist_ok=True)

    examples = [
        ("study.yaml.example", "study.yaml"),
        ("reader.yaml.example", "reader.yaml"),
        ("content.yaml.example", "content.yaml"),
    ]

    created_reader = False
    for example, target in examples:
        src = CONFIG_DIR / example
        dst = CONFIG_DIR / target

        if dst.exists() and not force:
            console.print(f"[dim]Skipping {target} (already exists)[/]")
            continue

        if src.exists():
            shutil.copy(src, dst)
            console.print(f"[green]Created config/{target}[/]")
            if target == "reader.yaml":
                created_reader = True
        else:
            console.print(f"[yellow]Warning: {example} not found[/]")

    # Prompt for API key if reader.yaml was created
    reader_yaml = CONFIG_DIR / "reader.yaml"
    if created_reader and reader_yaml.exists():
        console.print()
        api_key = Prompt.ask(
            "[bold]Enter your Google API key[/] (or press Enter to skip)",
            default="",
            show_default=False,
        )
        if api_key:
            with open(reader_yaml) as f:
                config = yaml.safe_load(f)
            config["llm"]["gemini"]["api_key"] = api_key
            with open(reader_yaml, "w") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            console.print("[green]API key saved to config/reader.yaml[/]")

    console.print("\n[bold]Setup complete![/]")
    console.print("Run [cyan]uv run knos read test[/] to verify LLM configuration.")
