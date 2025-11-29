# [Pattern Name]

> **"[Quote about the pattern]"**
> *[Brief tagline]*

## Overview

[Provide a brief description of the pattern. What problem does it solve? What are its key characteristics?]

## Architecture

```mermaid
---
config:
  layout: elk
  look: handDrawn
  theme: dark
---
graph TD
    User[User Request] --> Agent
    Agent -->|Action| Component[Component]
    Component -->|Result| Agent
    Agent -->|Final Response| User
    
    style Agent fill:#2d3748,stroke:#4a5568,color:#fff
    style Component fill:#2f855a,stroke:#48bb78,color:#fff
    style User fill:#4a5568,stroke:#718096,color:#fff
```

## Components

| Component | Description |
|-----------|-------------|
| **Agent** | [Description of the agent's role] |
| **[Component]** | [Description of the component] |

## How it Works

[Explain the mechanics of the pattern. How do the components interact?]

## When to Use

Use this pattern when your agent needs to:

- [Scenario 1]
- [Scenario 2]

## Try the Code

1. **Prerequisites**: Follow the [setup instructions](../../README.md#setup) in the root of the project.
2. **Run the Agent**:
    Run the following command in the root of the project:

    ```bash
    adk web patterns
    ```

3. **Select Pattern**: Click on **[Pattern Name]** in the sidebar to start the demo.

## Resources

- [Resource 1](https://example.com)
- [Resource 2](https://example.com)
