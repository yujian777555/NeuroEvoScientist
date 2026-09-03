# Architecture Genome

## Motivation

A fixed LLM backbone limits agent adaptation. EvoScientist-Mamba treats architecture as a searchable genome.

## Genome Example

```json
{
 "memory": {
   "type": "mamba",
   "state_size":128,
   "compression":"adaptive"
 },
 "reasoner": {
   "type":"attention",
   "layers":4
 },
 "tool_adapter": {
   "enabled":true
 }
}
```

## Search Dimensions

1. Memory substrate
- Mamba
- Attention cache
- Hybrid memory

2. Reasoning module
- Transformer block
- Lightweight reasoning block
- Mixture modules

3. Efficiency strategy
- Quantization
- Pruning
- Low rank adaptation

The genome enables evolutionary optimization of cognitive structures.
