"""
Action 4: Propose new mathematical objects and concepts

Flow: 4.a Input Memory → Output mathematical text → Jump to Action 2 to update memory
"""

from typing import Dict, Any
from llm_client import call_llm
from prompts.propose_objects import get_propose_objects_prompt, get_propose_objects_user_prompt
from memory import MemoryManager


class ProposeObjectsAction:
    """Action to propose new mathematical objects and concepts"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
    
    async def execute(self) -> Dict[str, Any]:
        """
        Execute propose new objects/concepts action (Action 4.a)
        
        Input: Memory
        Output: Mathematical text (new objects and concepts)
        
        Returns:
            Result containing mathematical text
        """
        system_prompt = get_propose_objects_prompt()
        user_prompt = get_propose_objects_user_prompt(
            memory_display=self.memory_manager.get_memory_display()
        )
        
        # Call LLM, get natural language output directly
        math_text = await call_llm(
            system_prompt=system_prompt,
            user_message=user_prompt,
            temperature=0.7  # Use higher temperature for creative tasks
        )
        
        return {
            "math_text": math_text,
            "action": "propose_objects"
        }
