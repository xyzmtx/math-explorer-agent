"""
Math Explorer Agent Data Model Definitions

Data Type Descriptions:
- Object (Mathematical Object): Is a "noun" in the mathematical world, is an Instance
- Concept (Mathematical Concept): Is a type/template (Class/Type), describes properties, categories, relationships, or structure of objects
- Direction (Exploration Direction): A clear direction for exploring conjectures, not necessarily a rigorous proposition
- Conjecture (Mathematical Conjecture): A rigorous mathematical proposition, to be proven
- Lemma (Conclusion): A proven mathematical proposition
"""

from dataclasses import dataclass, field
from typing import Optional, List, Literal
from enum import Enum
import json
from datetime import datetime


class ConfidenceLevel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass
class MathObject:
    """Mathematical Object - Instance"""
    id: str                          # Starting from obj_001
    name: str                        # Name (mathematical formula)
    type_and_definition: str         # Type & Definition
    comment: str = ""                # Comment (motivation, potential exploration directions)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type_and_definition": self.type_and_definition,
            "comment": self.comment
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "MathObject":
        return cls(**data)
    
    def to_display_string(self) -> str:
        return f"""【Mathematical Object {self.id}】
  Name: {self.name}
  Type & Definition: {self.type_and_definition}
  Comment: {self.comment}"""


@dataclass
class MathConcept:
    """Mathematical Concept - Type/Template (Class/Type)"""
    id: str                          # Starting from con_001
    name: str                        # Name
    definition: str                  # Definition
    comment: str = ""                # Comment (motivation, potential exploration directions)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "definition": self.definition,
            "comment": self.comment
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "MathConcept":
        return cls(**data)
    
    def to_display_string(self) -> str:
        return f"""【Mathematical Concept {self.id}】
  Name: {self.name}
  Definition: {self.definition}
  Comment: {self.comment}"""


@dataclass
class ExplorationDirection:
    """Exploration Direction"""
    id: str                          # Starting from dir_001
    description: str                 # Detailed description
    comment: str = ""                # Comment (motivation, potential solution paths)
    completely_solved: bool = False  # Whether this direction has been completely solved
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "comment": self.comment,
            "completely_solved": self.completely_solved
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ExplorationDirection":
        return cls(
            id=data["id"],
            description=data["description"],
            comment=data.get("comment", ""),
            completely_solved=data.get("completely_solved", False)
        )
    
    def to_display_string(self) -> str:
        solved_tag = " [COMPLETELY SOLVED]" if self.completely_solved else ""
        return f"""【Exploration Direction {self.id}】{solved_tag}
  Description: {self.description}
  Comment: {self.comment}"""


@dataclass
class MathConjecture:
    """Mathematical Conjecture"""
    id: str                          # Starting from conj_001
    statement: str                   # Rigorous mathematical proposition
    confidence_score: ConfidenceLevel = ConfidenceLevel.MEDIUM  # Confidence level
    comment: str = ""                # Comment (motivation, potential proof methods)
    completely_solved: bool = False  # Whether this conjecture has been completely solved (proven/disproven)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "statement": self.statement,
            "confidence_score": self.confidence_score.value if isinstance(self.confidence_score, ConfidenceLevel) else self.confidence_score,
            "comment": self.comment,
            "completely_solved": self.completely_solved
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "MathConjecture":
        confidence = data.get("confidence_score", "Medium")
        if isinstance(confidence, str):
            # Support both English and Chinese confidence levels
            confidence_map = {
                "High": ConfidenceLevel.HIGH, "Medium": ConfidenceLevel.MEDIUM, "Low": ConfidenceLevel.LOW,
                "高": ConfidenceLevel.HIGH, "中": ConfidenceLevel.MEDIUM, "低": ConfidenceLevel.LOW
            }
            confidence = confidence_map.get(confidence, ConfidenceLevel.MEDIUM)
        return cls(
            id=data["id"],
            statement=data["statement"],
            confidence_score=confidence,
            comment=data.get("comment", ""),
            completely_solved=data.get("completely_solved", False)
        )
    
    def to_display_string(self) -> str:
        score = self.confidence_score.value if isinstance(self.confidence_score, ConfidenceLevel) else self.confidence_score
        solved_tag = " [COMPLETELY SOLVED]" if self.completely_solved else ""
        return f"""【Mathematical Conjecture {self.id}】{solved_tag}
  Statement: {self.statement}
  Confidence: {score}
  Comment: {self.comment}"""


@dataclass
class MathLemma:
    """Conclusion (Proven Proposition)"""
    id: str                          # Starting from lem_001
    statement: str                   # Rigorous mathematical proposition
    proof: str = ""                  # Complete rigorous proof, "Conditional assumption" indicates original condition
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "statement": self.statement,
            "proof": self.proof
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "MathLemma":
        return cls(**data)
    
    def to_display_string(self) -> str:
        return f"""【Conclusion {self.id}】
  Statement: {self.statement}
  Proof: {self.proof}"""


@dataclass
class Memory:
    """Memory Storage Structure"""
    objects: List[MathObject] = field(default_factory=list)
    concepts: List[MathConcept] = field(default_factory=list)
    directions: List[ExplorationDirection] = field(default_factory=list)
    conjectures: List[MathConjecture] = field(default_factory=list)
    lemmas: List[MathLemma] = field(default_factory=list)
    
    # ID Counters
    _obj_counter: int = 0
    _con_counter: int = 0
    _dir_counter: int = 0
    _conj_counter: int = 0
    _lem_counter: int = 0
    
    def get_next_obj_id(self) -> str:
        self._obj_counter += 1
        return f"obj_{self._obj_counter:03d}"
    
    def get_next_con_id(self) -> str:
        self._con_counter += 1
        return f"con_{self._con_counter:03d}"
    
    def get_next_dir_id(self) -> str:
        self._dir_counter += 1
        return f"dir_{self._dir_counter:03d}"
    
    def get_next_conj_id(self) -> str:
        self._conj_counter += 1
        return f"conj_{self._conj_counter:03d}"
    
    def get_next_lem_id(self) -> str:
        self._lem_counter += 1
        return f"lem_{self._lem_counter:03d}"
    
    def to_dict(self) -> dict:
        return {
            "objects": [obj.to_dict() for obj in self.objects],
            "concepts": [con.to_dict() for con in self.concepts],
            "directions": [dir.to_dict() for dir in self.directions],
            "conjectures": [conj.to_dict() for conj in self.conjectures],
            "lemmas": [lem.to_dict() for lem in self.lemmas],
            "_obj_counter": self._obj_counter,
            "_con_counter": self._con_counter,
            "_dir_counter": self._dir_counter,
            "_conj_counter": self._conj_counter,
            "_lem_counter": self._lem_counter
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Memory":
        memory = cls()
        memory.objects = [MathObject.from_dict(obj) for obj in data.get("objects", [])]
        memory.concepts = [MathConcept.from_dict(con) for con in data.get("concepts", [])]
        memory.directions = [ExplorationDirection.from_dict(dir) for dir in data.get("directions", [])]
        memory.conjectures = [MathConjecture.from_dict(conj) for conj in data.get("conjectures", [])]
        memory.lemmas = [MathLemma.from_dict(lem) for lem in data.get("lemmas", [])]
        memory._obj_counter = data.get("_obj_counter", len(memory.objects))
        memory._con_counter = data.get("_con_counter", len(memory.concepts))
        memory._dir_counter = data.get("_dir_counter", len(memory.directions))
        memory._conj_counter = data.get("_conj_counter", len(memory.conjectures))
        memory._lem_counter = data.get("_lem_counter", len(memory.lemmas))
        return memory
    
    def to_display_string(self) -> str:
        """Generate complete Memory display string for prompts"""
        sections = []
        
        sections.append("=" * 60)
        sections.append("【Current Memory Content】")
        sections.append("=" * 60)
        
        # Mathematical Objects
        sections.append("\n## I. Mathematical Objects (Objects)")
        if self.objects:
            for obj in self.objects:
                sections.append(obj.to_display_string())
        else:
            sections.append("  (None)")
        
        # Mathematical Concepts
        sections.append("\n## II. Mathematical Concepts (Concepts)")
        if self.concepts:
            for con in self.concepts:
                sections.append(con.to_display_string())
        else:
            sections.append("  (None)")
        
        # Exploration Directions
        sections.append("\n## III. Exploration Directions (Directions)")
        if self.directions:
            for dir in self.directions:
                sections.append(dir.to_display_string())
        else:
            sections.append("  (None)")
        
        # Mathematical Conjectures
        sections.append("\n## IV. Mathematical Conjectures (Conjectures)")
        if self.conjectures:
            for conj in self.conjectures:
                sections.append(conj.to_display_string())
        else:
            sections.append("  (None)")
        
        # Conclusions
        sections.append("\n## V. Conclusions (Lemmas)")
        if self.lemmas:
            for lem in self.lemmas:
                sections.append(lem.to_display_string())
        else:
            sections.append("  (None)")
        
        sections.append("\n" + "=" * 60)
        
        return "\n".join(sections)
    
    def get_summary(self) -> str:
        """Get Memory summary"""
        return f"""Memory Summary:
- Mathematical Objects: {len(self.objects)}
- Mathematical Concepts: {len(self.concepts)}
- Exploration Directions: {len(self.directions)}
- Mathematical Conjectures: {len(self.conjectures)}
- Proven Conclusions: {len(self.lemmas)}"""


@dataclass
class ActionLog:
    """Action Log"""
    timestamp: str
    action_type: str
    action_id: str
    status: Literal["running", "completed", "failed"]
    description: str
    result_summary: str = ""
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "action_type": self.action_type,
            "action_id": self.action_id,
            "status": self.status,
            "description": self.description,
            "result_summary": self.result_summary
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ActionLog":
        return cls(**data)


@dataclass
class CoordinatorDecision:
    """Coordinator Decision"""
    decision_type: Literal["wait", "new_actions"]
    new_actions: List[dict] = field(default_factory=list)  # [{action_type, params}]
    reasoning: str = ""
    
    def to_dict(self) -> dict:
        return {
            "decision_type": self.decision_type,
            "new_actions": self.new_actions,
            "reasoning": self.reasoning
        }


# JSON Schema Definitions for Output Formats
MEMORY_UPDATE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "updates": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "enum": ["add", "modify", "mark_solved"]},
                    "entity_type": {"type": "string", "enum": ["object", "concept", "direction", "conjecture", "lemma"]},
                    "entity_id": {"type": "string"},
                    "data": {"type": "object"},
                    "reason": {"type": "string"}
                },
                "required": ["operation", "entity_type", "reason"]
            }
        },
        "summary": {"type": "string"}
    },
    "required": ["updates", "summary"]
}

PARSE_INPUT_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "objects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type_and_definition": {"type": "string"},
                    "comment": {"type": "string"}
                },
                "required": ["name", "type_and_definition"]
            }
        },
        "concepts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "definition": {"type": "string"},
                    "comment": {"type": "string"}
                },
                "required": ["name", "definition"]
            }
        },
        "directions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "comment": {"type": "string"}
                },
                "required": ["description"]
            }
        },
        "conjectures": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "statement": {"type": "string"},
                    "confidence_score": {"type": "string", "enum": ["High", "Medium", "Low"]},
                    "comment": {"type": "string"}
                },
                "required": ["statement"]
            }
        },
        "lemmas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "statement": {"type": "string"},
                    "proof": {"type": "string"}
                },
                "required": ["statement", "proof"]
            }
        }
    },
    "required": ["objects", "concepts", "directions", "conjectures", "lemmas"]
}
