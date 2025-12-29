"""
Action 6: Explore a mathematical exploration direction

Flow: 6.a Input Memory + direction → Output mathematical text → Jump to Action 2 to update memory
"""

from typing import Dict, Any
from llm_client import call_llm
from prompts.explore_direction import get_explore_direction_prompt, get_explore_direction_user_prompt
from memory import MemoryManager


class ExploreDirectionAction:
    """Action to explore a mathematical direction"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
    
    async def execute(self, direction_id: str) -> Dict[str, Any]:
        """
        Execute explore direction action (Action 6.a)
        
        Input: Memory + one mathematical exploration direction
        Output: Mathematical text
        
        Args:
            direction_id: ID of the direction to explore
            
        Returns:
            Result containing mathematical text
        """
        # Get direction info
        direction = self.memory_manager.get_direction_by_id(direction_id)
        if not direction:
            return {
                "error": f"Direction not found: {direction_id}",
                "math_text": "",
                "action": "explore_direction"
            }
        
        system_prompt = get_explore_direction_prompt()
        user_prompt = get_explore_direction_user_prompt(
            memory_display=self.memory_manager.get_memory_display(),
            direction_id=direction_id,
            direction_desc=direction.description
        )
        
        # Call LLM, get natural language output directly
        math_text = await call_llm(
            system_prompt=system_prompt,
            user_message=user_prompt,
            temperature=0.6
        )
        
        return {
            "direction_id": direction_id,
            "math_text": math_text,
            "action": "explore_direction"
        }
