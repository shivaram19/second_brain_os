#!/usr/bin/env python3
"""Generate a demo Obsidian vault for testing.

Creates a sample Obsidian vault at ~/ObsidianVault with 10 interconnected
notes covering Systems Thinking, Effective Altruism, Complex Systems, and
related topics. These notes include:
  - YAML frontmatter (title, tags, status, importance)
  - WikiLinks between related concepts
  - Markdown headings and structured content

Purpose:
  - Provide test data for the ingestion pipeline
  - Demonstrate Obsidian conventions (frontmatter, WikiLinks, tags)
  - Enable immediate evaluation of RAG and graph analytics

Usage:
    python scripts/generate_demo_vault.py
    brainos ingest
    brainos ask "How does systems thinking relate to effective altruism?"
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from brainos.core import Config

DEMO_VAULT_PATH = Path.home() / "ObsidianVault"

DEMO_NOTES = {
    "Systems Thinking": """---
title: Systems Thinking
tags: thinking, philosophy, methodology
status: active
importance: 9
---

Systems thinking is a holistic approach to problem-solving and understanding complex systems. It emphasizes understanding the interconnections and feedback loops between different components of a system, rather than analyzing each part in isolation.

## Key Principles

1. **Holism**: The whole is greater than the sum of its parts
2. **Interconnectedness**: Changes in one part affect the whole system
3. **Feedback Loops**: Positive and negative feedback shape system behavior
4. **Emergence**: Complex patterns emerge from simple rules

## Related Ideas

[[Effective Altruism]], [[Complex Systems]], [[Causal Models]]

Systems thinking is fundamental to [[Project Vidya]] and our approach to [[Long-term Planning]].
""",
    "Effective Altruism": """---
title: Effective Altruism
tags: ethics, impact, methodology
status: active
importance: 9
---

Effective Altruism (EA) is a philosophy and movement that uses evidence and reason to determine how to benefit others as much as possible. It combines the heart of altruism with the head of effectiveness.

## Core Tenets

1. **Impartiality**: Everyone's interests matter equally
2. **Cause Prioritization**: Use evidence to find the highest-impact causes
3. **Evidence-Based**: Empirical methods to measure impact
4. **Scalability**: Focus on problems that affect many people

## Impact Framework

We evaluate causes using: **Impact × Neglectedness × Solvability**

See [[Cause Prioritization]] and [[Long-term Thinking]].
""",
    "Complex Systems": """---
title: Complex Systems
tags: systems, science, methodology
status: active
importance: 7
---

A complex system is a system composed of many components which may interact with each other. Examples include the climate, economy, brain, immune system, and organizations.

## Characteristics

- Non-linear dynamics
- Emergent behavior
- Self-organization
- Feedback loops
- Adaptation

## Tools

- [[Agent-Based Modeling]]
- [[Network Analysis]]
- [[Information Theory]]

See also: [[Systems Thinking]], [[Causal Models]]
""",
    "Project Vidya": """---
title: Project Vidya
tags: project, learning, knowledge
status: active
importance: 8
---

Project Vidya is an initiative to build tools for knowledge synthesis and agentic reasoning over personal knowledge graphs.

## Goals

1. Build second brain infrastructure
2. Enable agentic workflows
3. Synthesize knowledge at scale

## Current Focus

- [[Second Brain OS]]
- Context engineering
- MCP integration

See: [[Systems Thinking]], [[Effective Altruism]]
""",
    "Cause Prioritization": """---
title: Cause Prioritization
tags: methodology, impact, strategy
status: active
importance: 7
---

Cause prioritization is the process of identifying and evaluating which causes to work on to maximize positive impact.

## Framework

Using [[Effective Altruism]] principles:

1. Scale: How many people are affected?
2. Neglectedness: How much work is already being done?
3. Solvability: How tractable is the problem?

## Examples

- [[Global Health]]
- [[AI Safety]]
- [[Institutional Reform]]

See also: [[Long-term Thinking]]
""",
    "Long-term Thinking": """---
title: Long-term Thinking
tags: strategy, philosophy, planning
status: active
importance: 8
---

Long-term thinking involves considering the implications of our actions far into the future and prioritizing problems affecting future generations.

## Key Questions

- What will matter 100 years from now?
- How do we avoid existential risks?
- What are our obligations to future people?

## Connection to EA

[[Effective Altruism]] emphasizes long-termism as a moral priority.

See: [[AI Safety]], [[Project Vidya]], [[Cause Prioritization]]
""",
    "Causal Models": """---
title: Causal Models
tags: methodology, logic, philosophy
status: active
importance: 6
---

Causal models formalize our understanding of cause-and-effect relationships. They help us reason about interventions and counterfactuals.

## Approaches

- Directed acyclic graphs (DAGs)
- Structural causal models (SCMs)
- Potential outcomes framework

## Use Cases

- Policy evaluation
- Scientific reasoning
- Impact measurement

See: [[Systems Thinking]], [[Statistics]]
""",
    "Second Brain OS": """---
title: Second Brain OS
tags: project, technology, knowledge
status: active
importance: 9
---

Second Brain OS is a local-first, agentic knowledge orchestration system built on Obsidian, Python, and MCP.

## Architecture

- [[Knowledge Layer]]: Vault + vectors + graph
- [[Instruction Layer]]: Persona + goals + framework
- [[Tool Layer]]: MCP servers

## Status

MVP in development. See [[Project Vidya]].

Built with: context engineering, hybrid retrieval, budget-aware packing
""",
    "Agent-Based Modeling": """---
title: Agent-Based Modeling
tags: methodology, simulation, complexity
status: active
importance: 5
---

Agent-based models simulate the actions and interactions of autonomous agents to assess their effects on the system as a whole.

## Applications

- Economic simulations
- Epidemiology
- Social dynamics
- Urban planning

See: [[Complex Systems]], [[Simulation]]
""",
    "Knowledge Layer": """---
title: Knowledge Layer
tags: architecture, technology
status: active
importance: 7
---

The Knowledge Layer of [[Second Brain OS]] comprises:

1. **Obsidian Vault**: Source of truth (markdown + frontmatter)
2. **Vector Index**: ChromaDB for semantic search
3. **Knowledge Graph**: NetworkX for structural relations
4. **RAG Engine**: Hybrid retrieval combining vectors + graph

See: [[Second Brain OS]], [[Systems Thinking]]
""",
}


def generate_vault():
    """Generate demo vault with sample notes."""
    vault_path = DEMO_VAULT_PATH
    vault_path.mkdir(parents=True, exist_ok=True)

    print(f"📝 Generating demo vault at: {vault_path}")

    for title, content in DEMO_NOTES.items():
        filename = title.lower().replace(" ", "_") + ".md"
        filepath = vault_path / filename

        with open(filepath, "w") as f:
            f.write(content)

        print(f"   ✓ {filename}")

    print(f"\n✅ Demo vault created with {len(DEMO_NOTES)} notes")
    print(f"   Path: {vault_path}")
    print(f"\n   Next: brainos ingest")


if __name__ == "__main__":
    generate_vault()
