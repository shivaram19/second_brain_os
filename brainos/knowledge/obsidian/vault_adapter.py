"""Adapter for reading Obsidian vault files.

VaultAdapter is the bridge between the filesystem (Obsidian vault) and the
knowledge layer. It reads markdown files, parses YAML frontmatter into dicts,
extracts WikiLinks for graph construction, and produces canonical Idea objects.

This is the first step in the ingestion pipeline: all downstream components
(chunkers, embedders, graph builders) consume Idea objects produced here.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from brainos.core.models import Idea
from uuid import uuid4
from datetime import datetime


class VaultAdapter:
    """Read and parse Obsidian vault files."""

    def __init__(self, vault_path: str | Path):
        """Initialize vault adapter.

        Args:
            vault_path: Path to Obsidian vault root
        """
        self.vault_path = Path(vault_path).expanduser()
        if not self.vault_path.exists():
            raise FileNotFoundError(f"Vault path not found: {self.vault_path}")

    def list_notes(self) -> List[Path]:
        """Get all markdown files in vault.

        Returns:
            List of Path objects for all .md files
        """
        return sorted(self.vault_path.glob("**/*.md"))

    def read_note(self, note_path: str | Path) -> Optional[Idea]:
        """Read a single note and parse into an Idea.

        Args:
            note_path: Path to note (relative to vault root or absolute)

        Returns:
            Parsed Idea object, or None if file not found
        """
        if isinstance(note_path, str):
            note_path = Path(note_path)

        # If relative, make it relative to vault
        if not note_path.is_absolute():
            note_path = self.vault_path / note_path

        if not note_path.exists():
            return None

        with open(note_path, "r", encoding="utf-8") as f:
            content = f.read()

        frontmatter, body = self._parse_frontmatter(content)
        title = frontmatter.get("title") or note_path.stem
        tags = frontmatter.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",")]

        vault_path_rel = note_path.relative_to(self.vault_path).as_posix()

        return Idea(
            id=uuid4(),
            title=title,
            content=body,
            frontmatter=frontmatter,
            tags=tags,
            created=datetime.utcnow(),
            modified=datetime.utcfromtimestamp(note_path.stat().st_mtime),
            vault_path=vault_path_rel,
        )

    def _parse_frontmatter(self, content: str) -> tuple[Dict[str, Any], str]:
        """Parse YAML frontmatter from markdown.

        Args:
            content: Full markdown content

        Returns:
            Tuple of (frontmatter dict, body string)
        """
        if not content.startswith("---"):
            return {}, content

        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}, content

        try:
            frontmatter = yaml.safe_load(parts[1]) or {}
        except yaml.YAMLError:
            frontmatter = {}

        body = parts[2].lstrip("\n")
        return frontmatter, body

    def extract_wikilinks(self, content: str) -> set[str]:
        """Extract WikiLinks from markdown content.

        Args:
            content: Markdown content

        Returns:
            Set of linked note names (without brackets)
        """
        pattern = r"\[\[([^\]]+)\]\]"
        matches = re.findall(pattern, content)
        return set(m.split("|")[0].strip() for m in matches)  # Handle aliases

    def ingest_all(self) -> List[Idea]:
        """Load all notes from vault.

        Returns:
            List of all Ideas from vault
        """
        ideas = []
        for note_path in self.list_notes():
            idea = self.read_note(note_path)
            if idea:
                ideas.append(idea)
        return ideas
