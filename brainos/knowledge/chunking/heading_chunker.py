"""Heading-based text chunking.

Splits markdown notes at heading boundaries (#, ##, etc.). This preserves
the document's semantic structure: each chunk contains a heading and its
associated body text, making chunks more meaningful for retrieval.

Used by the ingestion pipeline before embedding. Token counts are estimated
roughly (1 token ≈ 4 characters) for budget-aware context packing later.
"""

import re
from typing import Any, Dict, List
from uuid import UUID

from brainos.core.models import Chunk
from brainos.knowledge.chunker_base import AbstractChunker


class HeadingChunker(AbstractChunker):
    """Chunk text by Markdown headings."""

    def chunk(
        self, idea_id: UUID, text: str, metadata: Dict[str, Any] = None
    ) -> List[Chunk]:
        """Split text into chunks at heading boundaries.

        Args:
            idea_id: UUID of parent Idea
            text: Markdown text to chunk
            metadata: Optional metadata to attach

        Returns:
            List of Chunk objects
        """
        if metadata is None:
            metadata = {}

        chunks = []
        # Split on lines starting with #
        sections = re.split(r"^(#+\s+.+)$", text, flags=re.MULTILINE)

        chunk_index = 0
        i = 0
        while i < len(sections):
            # sections[i] is a heading (if i is odd), or body text
            if i % 2 == 1:  # This is a heading
                heading = sections[i]
                body = sections[i + 1] if i + 1 < len(sections) else ""
                chunk_text = heading + "\n" + body
            else:
                # No heading, just body
                chunk_text = sections[i]

            chunk_text = chunk_text.strip()
            if not chunk_text:
                i += 2 if i % 2 == 1 else 1
                continue

            # Estimate token count (rough: 1 token ≈ 4 chars)
            token_count = max(1, len(chunk_text) // 4)

            chunk = Chunk(
                idea_id=idea_id,
                text=chunk_text,
                chunk_index=chunk_index,
                token_count=token_count,
                metadata={**metadata, "chunking_strategy": "heading"},
            )
            chunks.append(chunk)
            chunk_index += 1

            i += 2 if i % 2 == 1 else 1

        return chunks
