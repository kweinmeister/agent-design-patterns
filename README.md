# Agent Design Patterns

![Agent Design Patterns](agent-design-patterns.gif)

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**A reference implementation of common architectural patterns for AI agents.**

This repository serves as an executable cookbook for building reliable, controlled, and effective AI agents using the [Google Agent Development Kit (ADK)](https://github.com/google/adk-python) and [Gemini](https://deepmind.google/technologies/gemini/).

> [!TIP]
> **View the Guide**: A static, non-interactive version of these patterns is available at [kweinmeister.github.io/agent-design-patterns](https://kweinmeister.github.io/agent-design-patterns).

---

## 🚀 Why Use This?

* **Architectural Blueprints**: Learn *how* to structure control flow for complex LLM tasks, moving beyond simple prompt engineering.
* **Google ADK Integration**: See best practices for using the Agent Development Kit in production-ready scenarios.
* **Inspectable Code**: Every pattern is a self-contained, runnable Python application (`agent.py`) with a matching UI, allowing you to trace exactly how the agent thinks and acts.
* **Pure Python**: Built with standard tools and easy-to-understand code.

---

## 📂 The Pattern Catalog

Each pattern demonstrates a specific control flow strategy to solve distinct types of problems.

| Pattern | Best For... |
| :--- | :--- |
| **[RAG](patterns/rag/)** | **Knowledge & Context.** augmenting the agent's knowledge with external data retrieval before generating a response. |
| **[Reflection](patterns/reflection/)** | **Quality Control.** Allowing an agent to critique and refine its own output to fix errors and catch hallucinations. |
| **[Sequential Agent](patterns/sequential/)** | **Process Automation.** Breaking a complex workflow into a linear chain of specialized sub-agents. |
| **[Tool Use](patterns/tool_use/)** | **Action Execution.** Giving an agent the ability to interact with the outside world via deterministic functions and APIs. |
| **[Voting](patterns/voting/)** | **Decision Making.** Generating multiple options in parallel and using a "judge" to select the best outcome. |
| **[Human in the Loop](patterns/human_in_the_loop/)** | **Safety & Approval.** Pausing execution to require human review before sensitive actions are taken. |
| **[Template](patterns/template/)** | **Experimentation.** A clean slate for building your own custom agent architectures. |

---

## ⚡ Getting Started

### Prerequisites

* Python 3.12+
* A Google Cloud API Key (for Gemini)

### Installation

We recommend using [uv](https://github.com/astral-sh/uv) for fast and reliable dependency management, but standard `pip` works as well.

1. **Clone the repository:**

    ```bash
    git clone https://github.com/kweinmeister/agent-design-patterns.git
    cd agent-design-patterns
    ```

2. **Configure Environment:**

    Copy the example environment file and add your API keys.

    ```bash
    cp .env.example .env
    ```

3. **Install Dependencies:**

    **Using uv (Recommended):**

    ```bash
    uv sync
    ```

    **Using pip:**

    ```bash
    pip install -r requirements.txt
    ```

### Running Locally

Start the interactive playground server:

```bash
# Using uv
uv run main.py

# Using python
python main.py
```

Access the interface at **`http://localhost:8000`**.

---

## 💬 Try the Interactive Chat

The repository includes a unified chat interface for testing all patterns.

1. **Start the Pattern Server**:

    ```bash
    adk web patterns
    ```

2. **Select a Pattern**:
    The UI will launch in your browser. Use the sidebar to switch between different agent architectures (e.g., RAG, Tool Use, Reflection).

3. **Run Scenarios**:
    Each pattern comes with pre-defined scenarios to help you understand its capabilities.

---

## ☁️ Deploying to Cloud Run

You can deploy the live, dynamic version to Google [Cloud Run](https://cloud.google.com/run).

1. **Set Configuration:**

    ```bash
    export GOOGLE_CLOUD_PROJECT=your-project-id
    export GOOGLE_CLOUD_LOCATION=us-central1
    export GEMINI_MODEL=gemini-2.5-flash
    export EMBEDDING_MODEL=gemini-embedding-001
    export RAG_DB_PATH=/tmp/rag_demo.db
    ```

2. **Deploy:**

    ```bash
    gcloud run deploy agent-patterns \
      --source . \
      --region $GOOGLE_CLOUD_LOCATION \
      --allow-unauthenticated \
      --set-env-vars GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,GOOGLE_CLOUD_LOCATION=$GOOGLE_CLOUD_LOCATION,GEMINI_MODEL=$GEMINI_MODEL,EMBEDDING_MODEL=$EMBEDDING_MODEL,RAG_DB_PATH=$RAG_DB_PATH
    ```

    > ⚠️ **Security Warning**: The `--allow-unauthenticated` flag makes your deployment public. Remove it for internal/production use.

---

## 🛠️ Contributing

Contributions are welcome! If you have a new pattern idea or want to improve an existing one, please check out our [contribution guidelines](CONTRIBUTING.md) (if available) or open an issue.

## 📄 License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.
