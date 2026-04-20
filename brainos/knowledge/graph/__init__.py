"""Knowledge graph construction and querying.

Builds a NetworkX directed graph from Obsidian vault links and tags.
Nodes represent ideas/concepts; edges represent relationships (links_to,
relates_to, supports, etc.). Graph traversal complements semantic search
by surfacing structurally important but semantically distant concepts.

GraphBuilder is the primary implementation. It also exposes analytics
(neighbors, PageRank, density) used by the ReflectionAgent.
"""
