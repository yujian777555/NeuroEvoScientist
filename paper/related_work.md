# Related Work and Novelty Positioning

## 1. AlphaEvolve and Evolutionary Discovery

AlphaEvolve demonstrates that LLM-driven evolutionary loops can discover and improve algorithms through candidate generation, automated evaluation, and iterative selection. Our work is inspired by this paradigm but changes the optimization target.

AlphaEvolve evolves executable algorithms/programs. NeuroEvoScientist evolves the cognitive substrate of AI agents, including memory, reasoning, tool-use, and efficiency components.

## 2. Neural Architecture Search

Traditional NAS focuses on finding better static neural architectures. Existing LLM-assisted NAS methods mainly optimize backbone structures or model configurations.

NeuroEvoScientist differs by treating an agent architecture as an evolving cognitive system rather than a static neural network.

## 3. Agent Architecture Search

Recent agent search methods optimize agent workflows, communication topology, or multi-agent organization.

Our focus is different:

- Workflow search: how agents cooperate.
- NeuroEvoScientist: how one agent's internal cognitive substrate evolves.

## 4. Mamba and State Space Models

Mamba provides an efficient long-context memory mechanism. In our framework, Mamba is not the main contribution but an evolvable memory component within the agent substrate.

## 5. AI Scientist Systems

Existing AI scientist systems focus on research automation, hypothesis generation, and experiment execution.

NeuroEvoScientist investigates whether the underlying agent architecture itself can evolve to become a better scientific researcher.

## Novelty Statement

We introduce Evolutionary Neural Substrate Search (ENSS), where the search target is not a program, model weight, or workflow, but the cognitive architecture of an intelligent agent.