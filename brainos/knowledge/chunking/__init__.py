"""Text chunking strategies.

Chunking breaks long markdown notes into semantically coherent segments.
Current implementations:
  - HeadingChunker: Splits at markdown headings (preserves structure)

Future strategies may include sliding-window, sentence-boundary, or
semantic-coherence chunkers. All implement AbstractChunker.
"""
