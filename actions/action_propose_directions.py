"""
Action 5: Propose new mathematical exploration directions

Flow: 5.a Input Memory → Output mathematical text → Jump to Action 2 to update memory
"""

from typing import Dict, Any
from llm_client import call_llm
from prompts.propose_directions import get_propose_directions_prompt, get_propose_directions_user_prompt
from memory import MemoryManager


class ProposeDirectionsAction:
    """Action to propose new exploration directions"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
    
    async def execute(self) -> Dict[str, Any]:
        """
        Execute propose new exploration directions action (Action 5.a)
        
        Input: Memory
        Output: Mathematical text (new exploration directions)
        
        Returns:
            Result containing mathematical text
        """
        system_prompt = get_propose_directions_prompt()
        user_prompt = get_propose_directions_user_prompt(
            memory_display=self.memory_manager.get_memory_display()
        )
        
        # Call LLM, get natural language output directly
        math_text = await call_llm(
            system_prompt=system_prompt,
            user_message=user_prompt,
            temperature=0.7
        )
        
        return {
            "math_text": math_text,
            "action": "propose_directions"
        }
