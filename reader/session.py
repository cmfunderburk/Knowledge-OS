"""Session persistence for reader dialogues.

Sessions are stored as:
  reader/sessions/<material-id>/ch<N>.jsonl   # Append-only transcript
  reader/sessions/<material-id>/ch<N>.meta.json  # Session metadata
"""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

# Base directory for sessions
SESSIONS_DIR = Path(__file__).parent / "sessions"


@dataclass
class Session:
    """A reading session for a chapter."""

    material_id: str
    chapter_num: int
    chapter_title: str
    started: datetime
    last_updated: datetime
    exchange_count: int = 0
    mode_distribution: dict[str, int] = field(default_factory=dict)
    insights: list[str] = field(default_factory=list)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    cache_tokens: int = 0

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "material_id": self.material_id,
            "chapter_num": self.chapter_num,
            "chapter_title": self.chapter_title,
            "started": self.started.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "exchange_count": self.exchange_count,
            "mode_distribution": self.mode_distribution,
            "insights": self.insights,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "cache_tokens": self.cache_tokens,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        """Create from dict (loaded from JSON)."""
        return cls(
            material_id=data["material_id"],
            chapter_num=data["chapter_num"],
            chapter_title=data["chapter_title"],
            started=datetime.fromisoformat(data["started"]),
            last_updated=datetime.fromisoformat(data["last_updated"]),
            exchange_count=data.get("exchange_count", 0),
            mode_distribution=data.get("mode_distribution", {}),
            insights=data.get("insights", []),
            total_input_tokens=data.get("total_input_tokens", 0),
            total_output_tokens=data.get("total_output_tokens", 0),
            cache_tokens=data.get("cache_tokens", 0),
        )


def _get_session_dir(material_id: str) -> Path:
    """Get session directory for a material."""
    return SESSIONS_DIR / material_id


def _get_transcript_path(material_id: str, chapter_num: int) -> Path:
    """Get path to transcript JSONL file."""
    return _get_session_dir(material_id) / f"ch{chapter_num:02d}.jsonl"


def _get_meta_path(material_id: str, chapter_num: int) -> Path:
    """Get path to metadata JSON file."""
    return _get_session_dir(material_id) / f"ch{chapter_num:02d}.meta.json"


def session_exists(material_id: str, chapter_num: int) -> bool:
    """Check if a session exists for this chapter."""
    return _get_meta_path(material_id, chapter_num).exists()


def load_session(material_id: str, chapter_num: int) -> Session | None:
    """Load session metadata, or None if no session exists."""
    meta_path = _get_meta_path(material_id, chapter_num)
    if not meta_path.exists():
        return None

    with open(meta_path) as f:
        data = json.load(f)
    return Session.from_dict(data)


def load_transcript(material_id: str, chapter_num: int) -> list[dict]:
    """Load transcript messages from JSONL file."""
    transcript_path = _get_transcript_path(material_id, chapter_num)
    if not transcript_path.exists():
        return []

    messages = []
    with open(transcript_path) as f:
        for line in f:
            line = line.strip()
            if line:
                messages.append(json.loads(line))
    return messages


def create_session(
    material_id: str,
    chapter_num: int,
    chapter_title: str,
) -> Session:
    """Create a new session (or return existing)."""
    existing = load_session(material_id, chapter_num)
    if existing:
        return existing

    now = datetime.now()
    session = Session(
        material_id=material_id,
        chapter_num=chapter_num,
        chapter_title=chapter_title,
        started=now,
        last_updated=now,
    )

    # Ensure directory exists
    session_dir = _get_session_dir(material_id)
    session_dir.mkdir(parents=True, exist_ok=True)

    # Write initial metadata
    save_metadata(session)

    return session


def save_metadata(session: Session) -> None:
    """Save session metadata to JSON file."""
    meta_path = _get_meta_path(session.material_id, session.chapter_num)
    meta_path.parent.mkdir(parents=True, exist_ok=True)

    with open(meta_path, "w") as f:
        json.dump(session.to_dict(), f, indent=2)


def append_message(
    material_id: str,
    chapter_num: int,
    role: str,
    content: str,
    mode: str,
    tokens: dict | None = None,
) -> None:
    """Append a message to the transcript (JSONL, append-only)."""
    transcript_path = _get_transcript_path(material_id, chapter_num)
    transcript_path.parent.mkdir(parents=True, exist_ok=True)

    message = {
        "role": role,
        "content": content,
        "mode": mode,
        "timestamp": datetime.now().isoformat(),
    }
    if tokens:
        message["tokens"] = tokens

    with open(transcript_path, "a") as f:
        f.write(json.dumps(message) + "\n")


def list_sessions(material_id: str) -> dict[int, Session]:
    """List all sessions for a material, keyed by chapter number."""
    session_dir = _get_session_dir(material_id)
    if not session_dir.exists():
        return {}

    sessions = {}
    for meta_file in session_dir.glob("ch*.meta.json"):
        # Extract chapter number from filename (ch01.meta.json -> 1)
        stem = meta_file.stem.replace(".meta", "")
        chapter_num = int(stem[2:])

        session = load_session(material_id, chapter_num)
        if session:
            sessions[chapter_num] = session

    return sessions
