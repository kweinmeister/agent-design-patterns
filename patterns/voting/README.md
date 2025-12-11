# Voting

> **"Quality emerges when variety meets discernment."**
> *Generate multiple perspectives in parallel and select the best outcome.*

## Overview

The **Voting / Best-of-N** pattern utilizes multiple agents (or the same agent with high temperature/diversity settings) to generate distinct attempts at the same prompt in parallel. A separate "Judge" or "Merger" agent then evaluates these options against a rubric to select the single best response.

This pattern is highly effective for creative tasks, brainstorming, or complex reasoning where a single inference path might get stuck in a local optimum.

## Architecture

```mermaid
---
config:
  layout: elk
  look: handDrawn
  theme: dark
---
graph TD
    User[User Request] --> Splitter
    Splitter --> AgentA[Humorous Agent]
    Splitter --> AgentB[Professional Agent]
    Splitter --> AgentC[Urgent Agent]
    
    AgentA --> OutputA[Option A]
    AgentB --> OutputB[Option B]
    AgentC --> OutputC[Option C]
    
    OutputA & OutputB & OutputC --> Judge[Judge Agent]
    Judge --> Final[Selected Winner]
    
    style Judge fill:#2f855a,stroke:#48bb78,color:#fff
    style User fill:#4a5568,stroke:#718096,color:#fff
    style AgentA fill:#2c5282,stroke:#4299e1,color:#fff
    style AgentB fill:#2c5282,stroke:#4299e1,color:#fff
    style AgentC fill:#2c5282,stroke:#4299e1,color:#fff
```

## Components

| Component | Description |
|-----------|-------------|
| **Parallel Agents** | A set of agents that receive the input. They can be identical (with high temperature) or configured with different personas/instructions to force diversity. |
| **Merger/Judge** | An agent responsible for reviewing all generated options and selecting the best one based on quality, accuracy, or specific criteria. |

## When to Use

Use this pattern when quality is paramount and you want to maximize the chance of a high-quality output by generating multiple candidates. It is particularly useful when subjectivity exists, as the "best" answer isn't strictly factual but depends on style or creativity. This approach also helps in reducing variance, as generating N options and picking one reduces the risk of a bad outlier compared to noisy individual LLM calls.

## Try the Demo

1. **Enter a Topic**: Type *"A smart collar that translates cat meows into English."*
2. **Parallel Generation**:
    - **Humorous Agent**: Writes a funny ad.
    - **Professional Agent**: Writes a serious ad.
    - **Urgent Agent**: Writes a "act now" ad.
3. **Judging**: The **Judge Agent** evaluates all three and highlights the winner with a reason.

## Resources

- [Google Cloud Architecture: Parallel Pattern](https://docs.cloud.google.com/architecture/choose-design-pattern-agentic-ai-system#parallel-pattern)
