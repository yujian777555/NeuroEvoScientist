# ENSS Algorithm Pipeline

## Evolutionary Neural Substrate Search

The full pipeline:

```
Initialize Agent Genome Population

        |
        v

Distributed Candidate Evaluation

        |
        v

Multi-objective Fitness Calculation

        |
        v

NSGA-III Pareto Selection

        |
        v

Mutation + Crossover

        |
        v

Weight Inheritance

        |
        v

Next Generation Agents
```

## Optimization Objectives

1. Capability
2. Efficiency
3. Memory efficiency
4. Adaptability

## Multi-GPU Strategy

Each A800 worker evaluates independent candidate agents.
The controller aggregates results and generates the next population.
