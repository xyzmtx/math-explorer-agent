"""
Action 1: Parse Input

Uses prompts to parse raw mathematical input and initialize Memory.
"""

from typing import Dict, Any
from llm_client import call_llm
from prompts.parse_input import get_parse_input_prompt, get_parse_input_user_prompt
from memory import MemoryManager


class ParseAction:
    """Parse raw input action"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
    
    async def execute(self, raw_input: str) -> Dict[str, Any]:
        """
        Execute parse action
        
        Args:
            raw_input: Raw mathematical text
            
        Returns:
            Parse result
        """
        system_prompt = get_parse_input_prompt()
        user_prompt = get_parse_input_user_prompt(raw_input)
        
        # Call LLM to parse
        result = await call_llm(
            system_prompt=system_prompt,
            user_message=user_prompt,
            expect_json=True,
            temperature=0.3
        )
        
        # Initialize Memory
        self._initialize_memory(result)
        
        return result
    
    def _initialize_memory(self, parsed_data: Dict[str, Any]):
        """Initialize Memory from parsed data"""
        # Add objects
        for obj in parsed_data.get("objects", []):
            self.memory_manager.add_object(
                name=obj.get("name", ""),
                type_and_definition=obj.get("type_and_definition", ""),
                comment=obj.get("comment", "")
            )
        
        # Add concepts
        for con in parsed_data.get("concepts", []):
            self.memory_manager.add_concept(
                name=con.get("name", ""),
                definition=con.get("definition", ""),
                comment=con.get("comment", "")
            )
        
        # Add exploration directions
        for dir_data in parsed_data.get("directions", []):
            self.memory_manager.add_direction(
                description=dir_data.get("description", ""),
                comment=dir_data.get("comment", "")
            )
        
        # Add conjectures
        for conj in parsed_data.get("conjectures", []):
            self.memory_manager.add_conjecture(
                statement=conj.get("statement", ""),
                confidence_score=conj.get("confidence_score", "Medium"),
                comment=conj.get("comment", "")
            )
        
        # Add conclusions (lemmas)
        for lem in parsed_data.get("lemmas", []):
            self.memory_manager.add_lemma(
                statement=lem.get("statement", ""),
                proof=lem.get("proof", "")
            )
