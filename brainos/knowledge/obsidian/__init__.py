"""Obsidian vault integration.

Provides the VaultAdapter for reading standard Obsidian markdown files,
parsing YAML frontmatter, extracting WikiLinks, and converting notes into
strongly-typed Idea objects for downstream processing.

Expects standard Obsidian conventions:
  - .md files with YAML frontmatter
  - WikiLinks in [[note-name]] format
  - Optional folder hierarchy
"""
