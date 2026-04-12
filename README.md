# Sales Intelligence Agent - System Architecture

This document visualizes the multi-agent architecture and data flow of the Sales Intelligence Agent system.

## High-Level Architecture

The system follows a sequential multi-agent orchestration pattern where each agent has a specific role, culminating in a highly refined response for the user.

```mermaid
graph TD
    %% User & UI Level
    User((User)) -->|Input Message| UI[Gradio Frontend\napp_gui.py]
    UI -->|AgentRequest| API[FastAPI Backend\nsales_agent.py]
    
    %% API Orchestration Level
    subgraph Multi-Agent Orchestrator
        API -->|1. Raw Input Context| Gating[Analyzer Agent\n'The Gatekeeper']
        
        Gating -->|Irrelevant Query| StopBranch([End Chat early])
        StopBranch -.-> API
        
        Gating -->|Relevant Query| Intent[Intent Summary]
        Intent -->|2. Approved Intent Context| Validator[Validator Agent\n'The Strategist']
        
        Validator -->|JSON Context| ValidatedData{Structured Context\n- Refined Request\n- Profile Updates\n- Priority}
        
        ValidatedData -->|3. Validated Context| SalesAgent[Sales Agent\n'The Expert']
        SalesAgent -->|Final Advice + JSON Updates| FinalResponse{Final Output\n- Agent Message\n- Recommendations\n- Next Steps}
    end
    
    %% External Data Sources
    subgraph Data & Tooling
        Tavily[(Tavily API)] -.->|Company News & Insights| API
        SME_DB[(Financial DNA\nCSV Dataset)] -.->|Sector Benchmarks| API
    end
    
    %% Outputs back to UI
    FinalResponse -->|AgentResponse| API
    API -->|Live Trace & Outputs| UI
    UI -->|Updates UI State| User
```

## Agent Roles & Responsibilities

### 1. Analyzer (Gatekeeper)
- **Model**: `llama-3.1-8b-instant` (Fast, low-latency)
- **Role**: Blocks small-talk and explicitly scopes the bounds of the conversation.
- **Output**: Returns either `[[[STOP]]]` for irrelevant content or a 1-sentence `INTENT SUMMARY` alongside `[[[PROCEED]]]` for valid queries.

### 2. Validator (Strategist)
- **Model**: `llama-3.1-8b-instant` (Fast formatting)
- **Role**: Consumes the Gatekeeper's intent summary, looks at the user's raw message, and structures the context into a rigorous JSON format.
- **Output**: Extracts data points to update the client's profile in the background and rewrites the user's request into a professional problem statement.

### 3. Sales Agent (The Expert Closer)
- **Model**: `llama-3.3-70b-versatile` (Heavy reasoning capability)
- **Role**: Uses the precise context from the Validator alongside sector financial benchmarks (`sme_financial_decision.csv`) and live data (`TavilyClient`) to generate a highly personalized, targeted response.
- **Output**: The conversational response displayed to the user, plus hidden JSON to drive UI suggestions (Recommendations and Next Steps).

## Data Normalization & Type Safety
To ensure resilience across multiple turns, the system intercepts all LLM output and enforces strict dictionary and list normalization before sending changes back to the Gradio UI State. By blocking raw Pydantic serialization of potentially contaminated memory buffers, the system avoids crashing during long dialogues.

## What Was Modified & Added

This diagram captures all the changes made on top of the original codebase during the hackathon session.

```mermaid
graph TD
    %% Original baseline
    Original["Original Codebase\n(Single-agent chat)"]

    %% Backend Refactor
    Original --> MA["Multi-Agent Refactor\nsales_agent.py"]
    MA --> A1["Analyzer Agent\nllama-3.1-8b-instant\nGates irrelevant input"]
    MA --> A2["Validator Agent\nllama-3.1-8b-instant\nStructures intent as JSON"]
    MA --> A3["Sales Agent\nllama-3.3-70b-versatile\nGenerates expert response"]

    A1 -->|"Feedforward: Approved Intent"| A2
    A2 -->|"Validated Sales Context"| A3

    %% JSON extraction
    MA --> JE["Robust JSON Extraction\nextract_json_block\nRegex-based, handles any LLM format"]
    MA --> TS["Type Safety Layer\nCoerces str to list for pain_points/goals\nCoerces str to float for budget/revenue"]
    MA --> TR["Trace Dict Added to AgentResponse\nanalyzer + validator outputs captured"]

    %% Gradio UI Upgrade
    Original --> GUI["Gradio UI Upgrade\napp_gui.py"]
    GUI --> G1["Gradio 6.0 Compatibility\nRemoved type=messages\nMoved theme to launch"]
    GUI --> G2["Dict-based History Normalization\nHandles ChatMessage objects\nPrevents second-turn crashes"]
    GUI --> G3["Intelligence Trace Panel\nCollapsible accordion\nShows Analyzer + Validator reasoning"]
    GUI --> G4["Safe Profile Serialization\nManual field extraction\nNo Pydantic model_dump crashes"]

    %% New Files
    Original --> NF["New Files Created"]
    NF --> NF1["smart_dashboard.py\nPlotSense Gradio dashboard\nCSV upload + AI chart generation"]
    NF --> NF2["final_api.py\nGradio client integration\nConnects to both services"]
    NF --> NF3["requirements.txt\nAll Python dependencies listed"]
    NF --> NF4["architecture.md\nSystem architecture docs"]
    NF --> NF5[".gitignore\nCovers Python, Node, Gradio, secrets"]

    %% Frontend
    Original --> FE["React Frontend\nfrontend/ - Vite + React 18"]
    FE --> FE1["config.js\nSalesGenius: 127.0.0.1:7860\nPlotSense: 127.0.0.1:7861"]
    FE --> FE2["Launcher Dashboard\nTwo service cards\nDirect links to Gradio apps"]
    FE --> FE3["HeroSection\nStats, CTA buttons"]
    FE --> FE4["Dark-mode Design System\nindex.css with CSS variables"]
    FE --> FE5["API Wrappers\nsalesGenius.js + plotSense.js"]
```


