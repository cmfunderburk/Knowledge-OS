"""
Reader commands - TUI and CLI utilities.

Provides the reader TUI and various utility commands for managing
reading materials and sessions.
"""
import shutil
import sys
from typing import Optional


def run_read_tui() -> None:
    """Launch the reader TUI."""
    try:
        from knos.tui.app import ReaderApp
        app = ReaderApp()
        app.run()
    except ImportError as e:
        print(f"Error starting reader TUI: {e}")
        print("Try running: uv run knos read")
        sys.exit(1)


def run_list() -> None:
    """List all registered materials."""
    from reader.config import load_registry

    registry = load_registry()
    if not registry.get("materials"):
        print("No materials registered. Add materials to reader/content_registry.yaml")
        return

    print("\nRegistered Materials:\n")
    for material_id, info in registry["materials"].items():
        title = info.get("title", material_id)
        author = info.get("author", "Unknown")
        chapters = len(info.get("structure", {}).get("chapters", []))
        print(f"  {material_id}")
        print(f"    {title} ({author})")
        print(f"    {chapters} chapters")
        print()


def run_clear(material_id: str, content: Optional[str] = None) -> None:
    """Clear session data for a material (or all materials if 'ALL').

    Args:
        material_id: Material ID or 'ALL' to clear everything
        content: Chapter number (e.g., '1') or appendix ID (e.g., 'A')
    """
    from reader.session import SESSIONS_DIR as sessions_root, _content_id_to_prefix

    if material_id.upper() == "ALL":
        # Clear everything
        if not sessions_root.exists():
            print("No sessions found.")
            return
        materials = list(sessions_root.iterdir())
        if not materials:
            print("No sessions found.")
            return
        shutil.rmtree(sessions_root)
        sessions_root.mkdir()
        print(f"Cleared all sessions ({len(materials)} materials)")
        return

    sessions_dir = sessions_root / material_id

    if not sessions_dir.exists():
        print(f"No sessions found for: {material_id}")
        return

    if content is not None:
        # Parse content ID (integer for chapters, string for appendices)
        try:
            content_id: int | str = int(content)
            label = f"chapter {content_id}"
        except ValueError:
            content_id = content.upper()
            label = f"appendix {content_id}"

        prefix = _content_id_to_prefix(content_id)
        files = [
            sessions_dir / f"{prefix}.jsonl",
            sessions_dir / f"{prefix}.meta.json",
        ]
        deleted = 0
        for f in files:
            if f.exists():
                f.unlink()
                deleted += 1
        if deleted:
            print(f"Cleared session for {material_id} {label}")
        else:
            print(f"No session found for {material_id} {label}")
    else:
        # Clear all sessions for this material
        shutil.rmtree(sessions_dir)
        print(f"Cleared all sessions for: {material_id}")


def run_test_llm() -> None:
    """Test LLM provider configuration."""
    from reader.llm import get_provider

    print("Testing LLM provider...")
    try:
        provider = get_provider()
        print(f"  Provider: {provider.__class__.__name__}")
        if hasattr(provider, "model_name"):
            print(f"  Model: {provider.model_name}")
        elif hasattr(provider, "model"):
            print(f"  Model: {provider.model}")

        print("\nSending test message...")
        response = provider.chat(
            messages=[{"role": "user", "content": "Say 'Hello from Reader!' and nothing else."}]
        )
        print(f"  Response: {response.text.strip()}")
        print("\nLLM integration working!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
