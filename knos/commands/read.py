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
        from tui.app import ReaderApp
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


def run_extract(material_id: str) -> None:
    """Extract chapters from a material."""
    from reader.content import extract_material

    print(f"Extracting: {material_id}")
    try:
        extract_material(material_id)
        print(f"Done. Check reader/extracted/{material_id}/")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def run_clear(material_id: str, chapter: Optional[int] = None) -> None:
    """Clear session data for a material (or all materials if 'ALL')."""
    # Get sessions root from reader module
    from reader.session import SESSIONS_DIR as sessions_root

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

    if chapter is not None:
        # Clear specific chapter
        files = [
            sessions_dir / f"ch{chapter:02d}.jsonl",
            sessions_dir / f"ch{chapter:02d}.meta.json",
        ]
        deleted = 0
        for f in files:
            if f.exists():
                f.unlink()
                deleted += 1
        if deleted:
            print(f"Cleared session for {material_id} chapter {chapter}")
        else:
            print(f"No session found for {material_id} chapter {chapter}")
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
        print(f"  Response: {response.strip()}")
        print("\nLLM integration working!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
