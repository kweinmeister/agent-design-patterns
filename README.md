# Agent Design Patterns

**A catalog of architectural patterns for building AI agents using the [Google Agent Development Kit (ADK)](https://github.com/google/adk) and [Gemini](https://deepmind.google/technologies/gemini/).**

This repository serves as a reference guide for engineering AI workflows. It provides executable implementations of common agentic architectures, allowing developers to test and inspect each design pattern.

---

## What are Agent Design Patterns?

Agent Design Patterns are architectural blueprints for structuring how Large Language Models process information. These patterns provide the necessary control flow to solve complex problems. By implementing architectures like self-correction loops or deterministic tool usage, developers can create systems that verify their own work and interact with external data, ensuring the final output adheres to specific constraints and business logic.

---

## 📂 The Pattern Catalog

Each pattern in this repository contains a self-contained ADK implementation (`agent.py`), a dedicated UI, and documentation.

| Pattern | Description |
| :--- | :--- |
| **[RAG](patterns/rag/)** | An agent that retrieves relevant information from a knowledge base to augment its context before generating a response. |
| **[Reflection](patterns/reflection/)** | An agent that critiques its own output to fix errors and improve quality. It utilizes a "Draft → Critique → Refine" loop to ensure accuracy before finalizing a response. |
| **[Sequential Agent](patterns/sequential/)** | An agent that executes a linear sequence of specialized sub-agents where the output of one step becomes the input for the next. |
| **[Tool Use](patterns/tool_use/)** | An agent equipped with executable functions (e.g., a calculator or API) to perform specific, deterministic tasks that fall outside the scope of text generation. |
| **[Voting](patterns/voting/)** | An agent that generates multiple options in parallel and selects the best one using a "judge" agent to ensure quality. |
| **[Human in the Loop](patterns/human_in_the_loop/)** | An agent that pauses execution to request user approval before performing sensitive actions (e.g., publishing content). |
| **[Template](patterns/template/)** | A standardized scaffold for creating and testing new agent patterns within this framework. |

---

## 🏗 Repository Architecture

You can use this application in two ways:

### 1. Live Application

This is the full experience. Whether running locally via `main.py` or [deployed to Cloud Run](#deploying-to-cloud-run), this is a dynamic **FastAPI** application. It loads the agents into memory and gives you an interactive playground to chat, run tools, and watch the reasoning loops unfold in real-time.

### 2. Static Documentation

For quick reference, the `docs/` folder contains a read-only snapshot of the app. We generate this using `build.py` to compile the repository state into static HTML, CSS, and JavaScript. This lets us host the examples directly on GitHub Pages without needing a backend server.

---

## ⚡ Getting Started

### Prerequisites

* Python 3.10+
* A Google Cloud API Key (for Gemini)

### Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/kweinmeister/agent-design-patterns.git
    cd agent-design-patterns
    ```

2. **Configure Environment:**

    Copy the example environment file and edit it with your API keys and configuration. See the [Google ADK Documentation](https://google.github.io/adk-docs/agents/models/#using-google-gemini-models) for more information.

    ```bash
    cp .env.example .env
    ```

3. **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

### Running Locally

Start the server to test the patterns interactively:

```bash
python main.py
```

Access the interface at **`http://localhost:8000`**.

### Deploying to Cloud Run

First, set your Google Cloud project configuration. note, you can also specify these in your `.env` file.

```bash
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_LOCATION=us-central1
export EMBEDDING_MODEL=gemini-embedding-001
export GEMINI_MODEL=gemini-2.5-flash
export RAG_DB_PATH=/tmp/rag_demo.db
```

Once you have tested the application locally, you can deploy the live, dynamic version to Google [Cloud Run](https://cloud.google.com/run):

```bash
gcloud run deploy agent-patterns \
  --source . \
  --region $GOOGLE_CLOUD_LOCATION \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,GOOGLE_CLOUD_LOCATION=$GOOGLE_CLOUD_LOCATION,EMBEDDING_MODEL=$EMBEDDING_MODEL,GEMINI_MODEL=$GEMINI_MODEL,RAG_DB_PATH=$RAG_DB_PATH
```

> ⚠️ The command above uses the `--allow-unauthenticated` flag, which makes your deployment publicly accessible. For production environments, remove this flag to restrict access.

### Building the Static Site

To regenerate the content in the `docs/` folder for static hosting:

```bash
python build.py
```
