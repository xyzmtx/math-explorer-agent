"""
Action 2: Update Memory
"""

import asyncio
from typing import Dict, Any, List
from llm_client import call_llm_safe
from prompts.update_memory import get_update_memory_prompt, get_update_memory_user_prompt
from memory import MemoryManager


class UpdateMemoryAction:
    """Action to update Memory"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
    
    async def execute(self, new_text: str) -> Dict[str, Any]:
        """
        Execute update action
        
        Args:
            new_text: New mathematical text (project progress)
            
        Returns:
            Update result
        """
        system_prompt = get_update_memory_prompt()
        user_prompt = get_update_memory_user_prompt(
            current_memory=self.memory_manager.get_memory_display(),
            new_text=new_text
        )
        
        # Use safe mode to call LLM
        default_result = {
            "updates": []
        }
        
        result = await call_llm_safe(
            system_prompt=system_prompt,
            user_message=user_prompt,
            default=default_result,
            temperature=0.3
        )
        
        # Apply updates
        update_results = self._apply_updates(result.get("updates", []))
        
        return {
            "updates_applied": update_results
        }
    
    def _apply_updates(self, updates: List[Dict[str, Any]]) -> List[str]:
        """Apply update operations"""
        return self.memory_manager.apply_updates(updates)
    
    async def update_from_structured_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update Memory from structured data (skip LLM analysis)
        
        Used to directly apply structured results from other actions
        """
        updates = []
        
        # Process new objects
        for obj in data.get("new_objects", []):
            updates.append({
                "operation": "add",
                "entity_type": "object",
                "data": {
                    "name": obj.get("name", ""),
                    "type_and_definition": obj.get("type_and_definition", ""),
                    "comment": obj.get("comment", obj.get("motivation", ""))
                },
                "reason": obj.get("motivation", "Newly discovered object")
            })
        
        # Process new concepts
        for con in data.get("new_concepts", []):
            updates.append({
                "operation": "add",
                "entity_type": "concept",
                "data": {
                    "name": con.get("name", ""),
                    "definition": con.get("definition", ""),
                    "comment": con.get("comment", con.get("motivation", ""))
                },
                "reason": con.get("motivation", "Newly discovered concept")
            })
        
        # Process new directions
        for dir_data in data.get("new_directions", []):
            updates.append({
                "operation": "add",
                "entity_type": "direction",
                "data": {
                    "description": dir_data.get("description", ""),
                    "comment": dir_data.get("comment", dir_data.get("motivation", ""))
                },
                "reason": dir_data.get("motivation", "Newly discovered exploration direction")
            })
        
        # Process new conjectures
        for conj in data.get("new_conjectures", []):
            updates.append({
                "operation": "add",
                "entity_type": "conjecture",
                "data": {
                    "statement": conj.get("statement", ""),
                    "confidence_score": conj.get("confidence_score", "Medium"),
                    "comment": conj.get("comment", "")
                },
                "reason": conj.get("evidence", "Newly discovered conjecture")
            })
        
        # Process new conclusions
        for lem in data.get("new_lemmas", []):
            updates.append({
                "operation": "add",
                "entity_type": "lemma",
                "data": {
                    "statement": lem.get("statement", ""),
                    "proof": lem.get("proof", "")
                },
                "reason": "Proven conclusion"
            })
        
        # Apply updates
        update_results = self._apply_updates(updates)
        
        return {
            "updates_applied": update_results,
            "summary": f"Applied {len(updates)} updates"
        }
