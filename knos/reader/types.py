"""
Shared type definitions for the reader module.
"""
from typing import TypeAlias

# Content identifier: integer for chapters, string for appendices, None for articles
ContentId: TypeAlias = int | str | None
