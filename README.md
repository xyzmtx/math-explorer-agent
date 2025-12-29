# Math Explorer Agent

An LLM-based semi-formal mathematical exploration agent for automating the exploration and proof process of mathematical problems.

## Core Philosophy

> **The essence of mathematical work can be divided into two aspects:**
> 1. **Discovering new meaningful mathematical objects** — Introducing key intermediate objects is an important step in completing certain proofs
> 2. **Discovering and proving relationships between objects** — Establishing connections between objects and concepts

This project automates mathematical exploration and proof by imitating mathematicians' work methods, utilizing strategies such as substructures, quotient structures, structure migration, and parameterization.

## System Architecture

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

## Quick Start

### 1. Install Dependencies

```bash
pip install httpx
```

### 2. Configure API

Edit `config.py`:

```python
API_KEY = 'your-api-key'
BASE_URL = 'https://your-api-url/v1'
MODEL = 'your-model-name'  # Recommend using models that support deep thinking
```

### 3. Run

```bash
# Interactive mode
python main.py

# Demo mode
python demo.py

# Batch mode
python main.py --input problem.txt --output ./results
```

## Memory Data Types

The system tracks all mathematical research progress by maintaining a structured Memory:

| Type | ID Format | Description | Example |
|------|-----------|-------------|---------|
| **memory_object** | obj_001 | Mathematical Object (Instance) | $n$ (integer), $f$ (function), $A$ (matrix) |
| **memory_concept** | con_001 | Mathematical Concept (Type/Proposition) | Prime number, Continuity, Group |
| **memory_direction** | dir_001 | Exploration Direction | Explore the relationship between $n$ and $n^2$ |
| **memory_conjecture** | conj_001 | Mathematical Conjecture (with confidence) | Conjecture: For all positive integers $n$, $n^2 \geq n$ |
| **memory_lemma** | lem_001 | Conclusion (Proven or Conditional Assumption) | Lemma: If $n > 1$, then $n^2 > n$ |

### Distinction Between Object and Concept

- **Object**: A "noun" in the mathematical world, the subject being operated on, measured, or studied - an **Instance**
  - Example: $n$ (an integer), $f(x)=x^2$ (a specific function)
  
- **Concept**: A description of properties, categories, relationships, or structures of objects - a **Type/Proposition**
  - Example: Prime number (Definition: A positive integer p is prime if and only if...), Continuity

## Agent Action Flow

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
| **8. Verify Proof** | Proof | Verification result | Segment-by-segment verification and modification |

### Data Flow

```
Action 3/4/5/6 ─→ Mathematical text ─→ Action 2 ─→ Update Memory

Action 7 ─→ Complete proof ─→ Action 8 ─┬→ Verification passed ─→ Action 2 (Conjecture to Conclusion)
                                        └→ Verification failed ─→ Action 8.b (Modify, up to 3 rounds)
                                                                   └→ Action 8.c (Accumulate attempts) ─→ Action 2 (Update comment)
```

## Project Structure

```
math_explorer_agent/
├── config.py              # Configuration file (API, parameters)
├── models.py              # Data model definitions
├── memory.py              # Memory manager
├── llm_client.py          # LLM client (supports safe calls)
├── coordinator.py         # Coordinator (action decisions)
├── agent.py               # Main Agent class (core logic)
├── main.py                # Command line entry point
├── demo.py                # Demo script
├── test_system.py         # System tests
│
├── prompts/               # Prompt templates
│   ├── parse_input.py     # Action 1: Parse input
│   ├── update_memory.py   # Action 2: Update Memory
│   ├── retrieval.py       # Action 3: Retrieve theory
│   ├── propose_objects.py # Action 4: Propose objects
│   ├── propose_directions.py # Action 5: Propose directions
│   ├── explore_direction.py  # Action 6: Explore direction
│   ├── solve_conjecture.py   # Action 7: Solve conjecture
│   ├── verify_proof.py       # Action 8: Verify proof
│   └── coordinator.py        # Coordinator
│
├── actions/               # Action implementations
│   ├── action_parse.py
│   ├── action_update.py
│   ├── action_retrieval.py
│   ├── action_propose_objects.py
│   ├── action_propose_directions.py
│   ├── action_explore.py
│   ├── action_solve.py
│   └── action_verify.py
│
└── memory_snapshots/      # Memory snapshot save directory
```

## Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `LLM_TIMEOUT` | 600 seconds | LLM call timeout (deep thinking models need more time) |
| `LLM_MAX_RETRIES` | 3 | Maximum retry count |
| `LLM_DEFAULT_MAX_TOKENS` | 65536 | Maximum token count (supports complex proofs) |
| `MAX_VERIFY_ROUNDS` | 3 | Maximum modification rounds for proof verification |
| `PROOF_CHUNK_SIZE` | 6 | Lines per verification segment |
| `MAX_PARALLEL_ACTIONS` | 10 | Maximum parallel actions per round |

## Usage Examples

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

## Human Checkpoint Mechanism

The system supports human intervention during automatic exploration:
- Pauses and asks user after running specified number of rounds
- User can choose: continue running, stop, or specify number of rounds to continue
- User can view Memory state and action log at any time

## Technical Features

1. **Parallel Execution**: Up to 10 actions execute in parallel per round, Memory lock ensures update atomicity
2. **Deep Thinking Model Optimization**: Simplified JSON output format with only core data fields
3. **Proof Verification**: Segment-by-segment verification (about 6 lines per segment), supports multiple modification rounds (up to 3)
4. **Experience Accumulation**: Automatically accumulates attempt experience on verification failure, updates conjecture comments

## License

MIT License

## Contributing

Issues and Pull Requests are welcome!
