# Reflection

> **"Critique is the secret to excellence."**
> *Iteratively improve response through self-correction.*

## Overview

The **Reflection** pattern enables an agent to critique its own outputs and refine them before delivering a final result. This approach mimics human self-editing, where a first draft is reviewed and improved to ensure accuracy, clarity, and adherence to constraints.

## Architecture

```mermaid
---
config:
  layout: elk
  look: handDrawn
  theme: dark
---
graph TD
    User[User Request] --> Generator
    Generator --> Draft[Draft Response]
    Draft --> Reflector
    Reflector --> Critique
    Critique --> Generator
    Generator --> Final[Final Response]
    
    subgraph "Reflection Loop"
    Generator
    Draft
    Reflector
    Critique
    end
    
    style Generator fill:#2d3748,stroke:#4a5568,color:#fff
    style Reflector fill:#2d3748,stroke:#4a5568,color:#fff
    style User fill:#4a5568,stroke:#718096,color:#fff
    style Final fill:#2f855a,stroke:#48bb78,color:#fff
```

## Components

| Component | Description |
|-----------|-------------|
| **Generator** | Produces the initial output based on the user's prompt. |
| **Critic** | Evaluates the output against specific criteria or general quality standards. |
| **Refiner** | Uses the critique to improve the output. |

## How it Works

The agent creates an initial response, then reviews its own work to identify errors or areas for improvement. Based on this critique, it generates a new version. This process repeats until a quality threshold is met or a maximum number of iterations is reached.

## When to Use

Use this pattern for complex tasks requiring high accuracy or adherence to strict constraints, such as code generation or creative writing. It is ideal when the cost of an error outweighs the cost of extra compute time, or when catching hallucinations and logical fallacies is critical.

## Try the Code

1. **Prerequisites**: Follow the [setup instructions](../../README.md#setup) in the root of the project.
2. **Run the Agent**:
    Run the following command in the root of the project:

    ```bash
    adk web patterns
    ```

3. **Select Pattern**: Click on **Reflection** in the sidebar to start the demo.

## Resources

- [Google Cloud Architecture: Iterative Refinement Pattern](https://docs.cloud.google.com/architecture/choose-design-pattern-agentic-ai-system#iterative-refinement-pattern)
- [ADK Documentation: Loop Agents](https://google.github.io/adk-docs/agents/workflow-agents/loop-agents/)
