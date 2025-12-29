"""
Memory Management Module
Responsible for Memory CRUD operations and persistent storage
"""

import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from models import (
    Memory, MathObject, MathConcept, ExplorationDirection,
    MathConjecture, MathLemma, ConfidenceLevel
)
from config import MEMORY_SAVE_PATH


class MemoryManager:
    """Memory Manager"""
    
    def __init__(self, save_path: str = MEMORY_SAVE_PATH):
        self.memory = Memory()
        self.save_path = save_path
        self._ensure_save_dir()
        self._version = 0  # Version number for tracking updates
        
    def _ensure_save_dir(self):
        """Ensure save directory exists"""
        os.makedirs(self.save_path, exist_ok=True)
    
    def get_memory(self) -> Memory:
        """Get current Memory"""
        return self.memory
    
    def get_memory_display(self) -> str:
        """Get Memory display string (for prompts)"""
        return self.memory.to_display_string()
    
    def get_memory_summary(self) -> str:
        """Get Memory summary"""
        return self.memory.get_summary()
    
    # ==================== Add Operations ====================
    
    def add_object(
        self,
        name: str,
        type_and_definition: str,
        comment: str = "",
        custom_id: Optional[str] = None
    ) -> MathObject:
        """Add mathematical object"""
        obj_id = custom_id or self.memory.get_next_obj_id()
        obj = MathObject(
            id=obj_id,
            name=name,
            type_and_definition=type_and_definition,
            comment=comment
        )
        self.memory.objects.append(obj)
        self._version += 1
        return obj
    
    def add_concept(
        self,
        name: str,
        definition: str,
        comment: str = "",
        custom_id: Optional[str] = None
    ) -> MathConcept:
        """Add mathematical concept"""
        con_id = custom_id or self.memory.get_next_con_id()
        concept = MathConcept(
            id=con_id,
            name=name,
            definition=definition,
            comment=comment
        )
        self.memory.concepts.append(concept)
        self._version += 1
        return concept
    
    def add_direction(
        self,
        description: str,
        comment: str = "",
        custom_id: Optional[str] = None
    ) -> ExplorationDirection:
        """Add exploration direction"""
        dir_id = custom_id or self.memory.get_next_dir_id()
        direction = ExplorationDirection(
            id=dir_id,
            description=description,
            comment=comment
        )
        self.memory.directions.append(direction)
        self._version += 1
        return direction
    
    def add_conjecture(
        self,
        statement: str,
        confidence_score: str = "Medium",
        comment: str = "",
        custom_id: Optional[str] = None
    ) -> MathConjecture:
        """Add mathematical conjecture"""
        conj_id = custom_id or self.memory.get_next_conj_id()
        
        # Convert confidence score
        confidence_map = {
            "High": ConfidenceLevel.HIGH,
            "Medium": ConfidenceLevel.MEDIUM,
            "Low": ConfidenceLevel.LOW,
            "高": ConfidenceLevel.HIGH,
            "中": ConfidenceLevel.MEDIUM,
            "低": ConfidenceLevel.LOW
        }
        confidence = confidence_map.get(confidence_score, ConfidenceLevel.MEDIUM)
        
        conjecture = MathConjecture(
            id=conj_id,
            statement=statement,
            confidence_score=confidence,
            comment=comment
        )
        self.memory.conjectures.append(conjecture)
        self._version += 1
        return conjecture
    
    def add_lemma(
        self,
        statement: str,
        proof: str = "",
        custom_id: Optional[str] = None
    ) -> MathLemma:
        """Add conclusion"""
        lem_id = custom_id or self.memory.get_next_lem_id()
        lemma = MathLemma(
            id=lem_id,
            statement=statement,
            proof=proof
        )
        self.memory.lemmas.append(lemma)
        self._version += 1
        return lemma
    
    # ==================== Find Operations ====================
    
    def get_object_by_id(self, obj_id: str) -> Optional[MathObject]:
        """Get mathematical object by ID"""
        for obj in self.memory.objects:
            if obj.id == obj_id:
                return obj
        return None
    
    def get_concept_by_id(self, con_id: str) -> Optional[MathConcept]:
        """Get mathematical concept by ID"""
        for con in self.memory.concepts:
            if con.id == con_id:
                return con
        return None
    
    def get_direction_by_id(self, dir_id: str) -> Optional[ExplorationDirection]:
        """Get exploration direction by ID"""
        for dir in self.memory.directions:
            if dir.id == dir_id:
                return dir
        return None
    
    def get_conjecture_by_id(self, conj_id: str) -> Optional[MathConjecture]:
        """Get mathematical conjecture by ID"""
        for conj in self.memory.conjectures:
            if conj.id == conj_id:
                return conj
        return None
    
    def get_lemma_by_id(self, lem_id: str) -> Optional[MathLemma]:
        """Get conclusion by ID"""
        for lem in self.memory.lemmas:
            if lem.id == lem_id:
                return lem
        return None
    
    # ==================== Modify Operations ====================
    
    def modify_object(self, obj_id: str, **kwargs) -> bool:
        """Modify mathematical object"""
        obj = self.get_object_by_id(obj_id)
        if obj:
            for key, value in kwargs.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            self._version += 1
            return True
        return False
    
    def modify_concept(self, con_id: str, **kwargs) -> bool:
        """Modify mathematical concept"""
        con = self.get_concept_by_id(con_id)
        if con:
            for key, value in kwargs.items():
                if hasattr(con, key):
                    setattr(con, key, value)
            self._version += 1
            return True
        return False
    
    def modify_direction(self, dir_id: str, **kwargs) -> bool:
        """Modify exploration direction"""
        direction = self.get_direction_by_id(dir_id)
        if direction:
            for key, value in kwargs.items():
                if hasattr(direction, key):
                    setattr(direction, key, value)
            self._version += 1
            return True
        return False
    
    def modify_conjecture(self, conj_id: str, **kwargs) -> bool:
        """Modify mathematical conjecture"""
        conj = self.get_conjecture_by_id(conj_id)
        if conj:
            for key, value in kwargs.items():
                if key == "confidence_score" and isinstance(value, str):
                    confidence_map = {
                        "High": ConfidenceLevel.HIGH,
                        "Medium": ConfidenceLevel.MEDIUM,
                        "Low": ConfidenceLevel.LOW,
                        "高": ConfidenceLevel.HIGH,
                        "中": ConfidenceLevel.MEDIUM,
                        "低": ConfidenceLevel.LOW
                    }
                    value = confidence_map.get(value, ConfidenceLevel.MEDIUM)
                if hasattr(conj, key):
                    setattr(conj, key, value)
            self._version += 1
            return True
        return False
    
    def modify_lemma(self, lem_id: str, **kwargs) -> bool:
        """Modify conclusion"""
        lem = self.get_lemma_by_id(lem_id)
        if lem:
            for key, value in kwargs.items():
                if hasattr(lem, key):
                    setattr(lem, key, value)
            self._version += 1
            return True
        return False
    
    # ==================== Mark as Completely Solved Operations ====================
    
    def mark_direction_solved(self, dir_id: str) -> bool:
        """Mark exploration direction as completely solved"""
        direction = self.get_direction_by_id(dir_id)
        if direction:
            direction.completely_solved = True
            self._version += 1
            return True
        return False
    
    def mark_conjecture_solved(self, conj_id: str) -> bool:
        """Mark mathematical conjecture as completely solved"""
        conj = self.get_conjecture_by_id(conj_id)
        if conj:
            conj.completely_solved = True
            self._version += 1
            return True
        return False
    
    # ==================== Delete Operations (for objects, concepts, lemmas only) ====================
    
    def delete_object(self, obj_id: str) -> bool:
        """Delete mathematical object"""
        for i, obj in enumerate(self.memory.objects):
            if obj.id == obj_id:
                self.memory.objects.pop(i)
                self._version += 1
                return True
        return False
    
    def delete_concept(self, con_id: str) -> bool:
        """Delete mathematical concept"""
        for i, con in enumerate(self.memory.concepts):
            if con.id == con_id:
                self.memory.concepts.pop(i)
                self._version += 1
                return True
        return False
    
    def delete_lemma(self, lem_id: str) -> bool:
        """Delete conclusion"""
        for i, lem in enumerate(self.memory.lemmas):
            if lem.id == lem_id:
                self.memory.lemmas.pop(i)
                self._version += 1
                return True
        return False
    
    # ==================== Batch Update ====================
    
    def apply_updates(self, updates: List[Dict[str, Any]]) -> List[str]:
        """
        Apply batch updates
        
        updates format: [
            {
                "operation": "add" | "modify" | "mark_solved",
                "entity_type": "object" | "concept" | "direction" | "conjecture" | "lemma",
                "entity_id": "xxx" (required for modify/mark_solved),
                "data": {...} (required for add/modify),
                "reason": "update reason"
            }
        ]
        
        Note: mark_solved is only applicable for direction and conjecture types.
        """
        results = []
        
        for update in updates:
            op = update.get("operation")
            entity_type = update.get("entity_type")
            entity_id = update.get("entity_id")
            data = update.get("data", {})
            reason = update.get("reason", "")
            
            try:
                if op == "add":
                    result = self._add_entity(entity_type, data)
                    results.append(f"✓ Added {entity_type}: {result.id} - {reason}")
                elif op == "modify":
                    success = self._modify_entity(entity_type, entity_id, data)
                    if success:
                        results.append(f"✓ Modified {entity_type} {entity_id} - {reason}")
                    else:
                        results.append(f"✗ Modify failed {entity_type} {entity_id}: Not found")
                elif op == "mark_solved":
                    success = self._mark_entity_solved(entity_type, entity_id)
                    if success:
                        results.append(f"✓ Marked {entity_type} {entity_id} as completely solved - {reason}")
                    else:
                        results.append(f"✗ Mark solved failed {entity_type} {entity_id}: Not found or not applicable")
            except Exception as e:
                results.append(f"✗ Operation failed {op} {entity_type}: {str(e)}")
        
        return results
    
    def _add_entity(self, entity_type: str, data: Dict[str, Any]):
        """Add entity"""
        if entity_type == "object":
            return self.add_object(**data)
        elif entity_type == "concept":
            return self.add_concept(**data)
        elif entity_type == "direction":
            return self.add_direction(**data)
        elif entity_type == "conjecture":
            return self.add_conjecture(**data)
        elif entity_type == "lemma":
            return self.add_lemma(**data)
        else:
            raise ValueError(f"Unknown entity type: {entity_type}")
    
    def _modify_entity(self, entity_type: str, entity_id: str, data: Dict[str, Any]) -> bool:
        """Modify entity"""
        if entity_type == "object":
            return self.modify_object(entity_id, **data)
        elif entity_type == "concept":
            return self.modify_concept(entity_id, **data)
        elif entity_type == "direction":
            return self.modify_direction(entity_id, **data)
        elif entity_type == "conjecture":
            return self.modify_conjecture(entity_id, **data)
        elif entity_type == "lemma":
            return self.modify_lemma(entity_id, **data)
        else:
            raise ValueError(f"Unknown entity type: {entity_type}")
    
    def _delete_entity(self, entity_type: str, entity_id: str) -> bool:
        """Delete entity (only for objects, concepts, lemmas)"""
        if entity_type == "object":
            return self.delete_object(entity_id)
        elif entity_type == "concept":
            return self.delete_concept(entity_id)
        elif entity_type == "lemma":
            return self.delete_lemma(entity_id)
        else:
            raise ValueError(f"Delete not supported for entity type: {entity_type}. Use mark_solved for directions and conjectures.")
    
    def _mark_entity_solved(self, entity_type: str, entity_id: str) -> bool:
        """Mark entity as completely solved (only for directions and conjectures)"""
        if entity_type == "direction":
            return self.mark_direction_solved(entity_id)
        elif entity_type == "conjecture":
            return self.mark_conjecture_solved(entity_id)
        else:
            raise ValueError(f"Mark solved not supported for entity type: {entity_type}")
    
    # ==================== Persistence ====================
    
    def save(self, filename: Optional[str] = None) -> str:
        """Save Memory to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"memory_{timestamp}.json"
        
        filepath = os.path.join(self.save_path, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.memory.to_dict(), f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def load(self, filepath: str) -> bool:
        """Load Memory from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.memory = Memory.from_dict(data)
            return True
        except Exception as e:
            print(f"Failed to load Memory: {e}")
            return False
    
    def get_version(self) -> int:
        """Get current version number"""
        return self._version
    
    def convert_conjecture_to_lemma(self, conj_id: str, proof: str) -> Optional[MathLemma]:
        """Convert conjecture to conclusion (marks conjecture as solved instead of deleting)"""
        conj = self.get_conjecture_by_id(conj_id)
        if conj:
            lemma = self.add_lemma(
                statement=conj.statement,
                proof=proof
            )
            self.mark_conjecture_solved(conj_id)
            return lemma
        return None
