# Math Explorer Agent 🔬

An LLM-powered semi-formal mathematical exploration agent that automates the discovery and proof process of mathematical problems through structured reasoning and parallel action execution.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)

---

## 🌟 Core Philosophy

> **The essence of mathematical work can be divided into two aspects:**
> 1. **Discovering new meaningful mathematical objects** — Introducing key intermediate objects is an important step in completing certain proofs
> 2. **Discovering and proving relationships between objects** — Establishing connections between objects and concepts

This project automates mathematical exploration and proof by imitating mathematicians' work methods, utilizing strategies such as substructures, quotient structures, structure migration, and parameterization.

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                        Math Explorer Agent                      │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│   │  User Input  │ ─→ │ Parse Input  │ ─→ │    Memory    │     │
│   │ (Math Problem)│   │  (Action 1)  │    │ (Structured) │     │
│   └──────────────┘    └──────────────┘    └──────┬───────┘     │
│                                                   │              │
│   ┌───────────────────────────────────────────────▼───────────┐ │
│   │                   Coordinator                              │ │
│   │  Analyzes Memory state, decides parallel actions per round │ │
│   │  (up to 10 actions)                                        │ │
│   └───────────────────────────────────────────────────────────┘ │
│                              │                                   │
│       ┌──────────────────────┼──────────────────────┐           │
│       ▼                      ▼                      ▼           │
│   ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐   │
│   │Retrieval│ │Propose │  │Propose │  │Explore │  │ Solve  │   │
│   │(Action3)│ │Objects │  │Directions│ │Direction│ │Conjecture│ │
│   │        │  │(Action4)│ │(Action5)│ │(Action6)│ │(Action7)│   │
│   └───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘   │
│       │           │           │           │           │         │
│       └───────────┴───────────┴───────────┴───────────┘         │
│                              │                                   │
│                              ▼                                   │
│                    ┌──────────────────┐                         │
│                    │  Update Memory   │ ←─── Verify & Modify    │
│                    │    (Action 2)    │       (Action 8)        │
│                    └──────────────────┘                         │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
math_explorer_agent_english/
├── config.py                 # Configuration (API keys, parameters)
├── models.py                 # Data model definitions
├── memory.py                 # Memory manager (CRUD operations)
├── llm_client.py             # LLM client (async, retry, JSON parsing)
├── coordinator.py            # Coordinator (action decisions)
├── agent.py                  # Main Agent class (core logic)
├── main.py                   # Command line entry point
├── server.py                 # Flask web server (REST API + SSE)
│
├── prompts/                  # Prompt templates
│   ├── __init__.py
│   ├── parse_input.py        # Action 1: Parse input
│   ├── update_memory.py      # Action 2: Update Memory
│   ├── retrieval.py          # Action 3: Retrieve theory
│   ├── propose_objects.py    # Action 4: Propose objects
│   ├── propose_directions.py # Action 5: Propose directions
│   ├── explore_direction.py  # Action 6: Explore direction
│   ├── solve_conjecture.py   # Action 7: Solve conjecture
│   ├── verify_proof.py       # Action 8: Verify proof
│   └── coordinator.py        # Coordinator prompts
│
├── actions/                  # Action implementations
│   ├── __init__.py
│   ├── action_parse.py
│   ├── action_update.py
│   ├── action_retrieval.py
│   ├── action_propose_objects.py
│   ├── action_propose_directions.py
│   ├── action_explore.py
│   ├── action_solve.py
│   └── action_verify.py
│
├── website/                  # Web frontend
│   ├── index.html            # Main HTML page
│   ├── styles.css            # CSS styles
│   └── app.js                # JavaScript application
│
├── memory_snapshots/         # Memory snapshot storage
│
├── requirements.txt          # Python dependencies
├── Procfile                  # Render deployment config
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
├── DEPLOY.md                 # Deployment tutorial
└── README.md                 # This file
```

---

## 🚀 Quick Start

### 1. Clone and Install Dependencies

```bash
git clone https://github.com/yourusername/math-explorer-agent.git
cd math-explorer-agent

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API

Copy the example environment file and edit it:

```bash
cp .env.example .env
```

Edit `.env` with your API credentials:

```env
# Option 1: Paratera (DeepSeek)
API_KEY=your-api-key-here
BASE_URL=https://ai.paratera.com/v1
MODEL=DeepSeek-V3.2

# Option 2: OpenAI
# API_KEY=sk-xxx
# BASE_URL=https://api.openai.com/v1
# MODEL=gpt-4
```

### 3. Run the Application

**Web Interface (Recommended):**
```bash
python server.py
# Open http://localhost:5000/website/ in your browser
```

**Command Line Interface:**
```bash
# Interactive mode
python main.py

# Batch mode
python main.py --input problem.txt --output ./results --max-rounds 50
```

---

## 📊 Memory Data Types

The system tracks all mathematical research progress by maintaining a structured Memory:

| Type | ID Format | Description | Example |
|------|-----------|-------------|---------|
| **Object** | `obj_001` | Mathematical Object (Instance) | $n$ (integer), $f$ (function), $A$ (matrix) |
| **Concept** | `con_001` | Mathematical Concept (Type/Proposition) | Prime number, Continuity, Group |
| **Direction** | `dir_001` | Exploration Direction | Explore the relationship between $n$ and $n^2$ |
| **Conjecture** | `conj_001` | Mathematical Conjecture (with confidence) | Conjecture: For all positive integers $n$, $n^2 ≥ n$ |
| **Lemma** | `lem_001` | Proven Conclusion | Lemma: If $n > 1$, then $n^2 > n$ |

### Object vs Concept

- **Object**: A "noun" in the mathematical world, the subject being operated on, measured, or studied — an **Instance**
  - Example: $n$ (a specific integer), $f(x)=x^2$ (a specific function)
  
- **Concept**: A description of properties, categories, relationships, or structures of objects — a **Type/Proposition**
  - Example: Prime number (Definition: A positive integer p is prime if and only if...), Continuity

---

## ⚡ Agent Actions

### Action List

| Action | Input | Output | Description |
|--------|-------|--------|-------------|
| **1. Parse Input** | Raw mathematical text | Structured entities | Initialize Memory |
| **2. Update Memory** | Mathematical text | Update instructions | Merge/Modify/Mark Solved entities |
| **3. Retrieve Theory** | Memory | Mathematical text | Retrieve related mathematical theories |
| **4. Propose Objects** | Memory | Mathematical text | Discover new mathematical objects/concepts |
| **5. Propose Directions** | Memory | Mathematical text | Discover new exploration directions |
| **6. Explore Direction** | Memory + direction_id | Mathematical text | Deep exploration of a direction |
| **7. Solve Conjecture** | Memory + conjecture_id | Mathematical text/Proof | Prove or disprove conjecture |
| **8. Verify Proof** | Proof | Verification result | Segment-by-segment verification |

### Data Flow

```
Action 3/4/5/6 ─→ Mathematical text ─→ Action 2 ─→ Update Memory

Action 7 ─→ Complete proof ─→ Action 8 ─┬→ Verification passed ─→ Action 2 (Conjecture to Conclusion)
                                        └→ Verification failed ─→ Action 8.b (Modify, up to 3 rounds)
                                                                   └→ Action 8.c (Accumulate attempts) ─→ Action 2
```

---

## 🌐 Web Interface

The web interface provides real-time visualization of the exploration process:

### Features
- **Real-time Updates**: Server-Sent Events (SSE) for live action tracking
- **Memory Visualization**: Interactive view of Objects, Concepts, Directions, Conjectures, and Lemmas
- **Action Logs**: Detailed logs of all agent activities
- **Checkpoint Control**: Human intervention points for exploration control

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Get current agent status |
| `/api/start` | POST | Initialize exploration with math text |
| `/api/run` | POST | Run exploration rounds |
| `/api/memory` | GET | Get current memory state |
| `/api/stop` | POST | Stop current exploration |
| `/api/events` | GET | SSE stream for real-time updates |

---

## ⚙️ Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `LLM_TIMEOUT` | 600s | LLM call timeout (deep thinking models need more time) |
| `LLM_MAX_RETRIES` | 3 | Maximum retry count |
| `LLM_DEFAULT_MAX_TOKENS` | 32768 | Maximum token count |
| `LLM_DEFAULT_TEMPERATURE` | 0.7 | Default sampling temperature |
| `MAX_VERIFY_ROUNDS` | 3 | Maximum proof modification rounds |
| `PROOF_CHUNK_SIZE` | 6 | Lines per verification segment |
| `MAX_PARALLEL_ACTIONS` | 10 | Maximum parallel actions per round |

---

## 💡 Usage Examples

### Interactive Mode

```bash
python main.py
```

1. Enter mathematical problem (end with `END`)
2. System parses and initializes Memory
3. Choose automatic exploration or manual mode
4. During automatic exploration, will ask whether to continue every N rounds

### Batch Mode

```bash
python main.py --input problem.txt --output ./results --max-rounds 50 --checkpoint 10
```

### Manual Commands

Available commands in manual mode:
- `show` - Display current Memory
- `add` - Manually add action
- `text` - Add mathematical text
- `run N [C]` - Run N rounds (check every C rounds)
- `save` - Save Memory
- `quit` - Exit

---

## 🤖 Human Checkpoint Mechanism

The system supports human intervention during automatic exploration:
- Pauses and asks user after running specified number of rounds
- User can choose: continue running, stop, or specify number of rounds to continue
- User can view Memory state and action log at any time

---

## 🔧 Technical Features

1. **Parallel Execution**: Up to 10 actions execute in parallel per round, Memory lock ensures update atomicity
2. **Deep Thinking Model Support**: Automatically filters thinking process, extracts final answer
3. **Robust JSON Parsing**: Multi-level fallback with truncation recovery
4. **Proof Verification**: Segment-by-segment verification (about 6 lines per segment), supports multiple modification rounds
5. **Experience Accumulation**: Automatically accumulates attempt experience on verification failure

---

## ☁️ Cloud Deployment

### Deploy to Render (Free Tier)

1. Push code to GitHub
2. Create new Web Service on [Render](https://render.com)
3. Connect GitHub repository
4. Set environment variables:
   - `API_KEY`: Your LLM API key
   - `BASE_URL`: API endpoint
   - `MODEL`: Model name
   - `DEBUG`: `false`
5. Start Command: `gunicorn server:app --bind 0.0.0.0:$PORT --timeout 600`

See [DEPLOY.md](DEPLOY.md) for detailed deployment instructions.

---

## 🔒 Security Notes

⚠️ **Never commit API keys to Git!**

- `.env` file is ignored by `.gitignore`
- Only `.env.example` (without real keys) is uploaded
- Real keys should only exist in:
  - Local `.env` file
  - Cloud platform environment variables

---

## 🛠️ Supported LLM Providers

| Provider | Models | Notes |
|----------|--------|-------|
| **Paratera** | DeepSeek-V3.2, DeepSeek-V3.2-Thinking | Recommended for thinking models |
| **OpenAI** | GPT-4, GPT-4-Turbo | Standard API |
| **YeysAI** | Gemini-3-pro-preview-thinking | Alternative provider |
| **Any OpenAI-compatible API** | - | Custom BASE_URL supported |

---

## 📝 License

MIT License

---

## 🤝 Contributing

Issues and Pull Requests are welcome!

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/math-explorer-agent.git
cd math-explorer-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your API credentials

# Run in development mode
python server.py
```

---

## 📚 How It Works

### 1. Input Parsing
When you input a mathematical problem, the agent uses Action 1 (Parse Input) to extract:
- Mathematical Objects (variables, functions, etc.)
- Concepts (definitions, properties)
- Exploration Directions (research paths)
- Conjectures (propositions to prove)
- Known Lemmas (established facts)

### 2. Coordinator Decision
The Coordinator analyzes the current Memory state and decides which actions to execute in parallel. It considers:
- Available unsolved conjectures
- Unexplored directions
- Memory richness (whether more objects/concepts are needed)

### 3. Parallel Exploration
Each round, up to 10 actions can execute simultaneously:
- **Retrieval**: Gather relevant mathematical theories
- **Propose Objects/Directions**: Generate new research paths
- **Explore Direction**: Deep dive into specific areas
- **Solve Conjecture**: Attempt proofs

### 4. Memory Updates
All action outputs (mathematical text) are processed by Action 2 (Update Memory), which:
- Adds new entities to Memory
- Modifies existing entities with new information
- Marks solved directions/conjectures

### 5. Proof Verification
When a proof is generated:
1. **Segment Verification**: Proof is split into chunks and verified
2. **Automatic Modification**: Failed segments are modified (up to 3 rounds)
3. **Result Recording**: Successful proofs upgrade conjectures to lemmas

---

## ⭐ Star History

If you find this project useful, please consider giving it a star! ⭐
