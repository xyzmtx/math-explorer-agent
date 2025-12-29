"""
Action 3: Update Memory through Retrieval

Flow: 3.a Input Memory → Output mathematical text → Jump to Action 2 to update memory
"""

from typing import Dict, Any
from llm_client import call_llm
from prompts.retrieval import get_retrieval_prompt, get_retrieval_user_prompt
from memory import MemoryManager


class RetrievalAction:
    """Action to retrieve related mathematical theories"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
    
    async def execute(self) -> Dict[str, Any]:
        """
        Execute retrieval action (Action 3.a)
        
        Input: Memory
        Output: Mathematical text (retrieved related theories)
        
        Returns:
            Result containing mathematical text
        """
        system_prompt = get_retrieval_prompt()
        user_prompt = get_retrieval_user_prompt(
            memory_display=self.memory_manager.get_memory_display()
        )
        
        # Call LLM, get natural language output directly
        math_text = await call_llm(
            system_prompt=system_prompt,
            user_message=user_prompt,
            temperature=0.5
        )
        
        return {
            "math_text": math_text,
            "action": "retrieval"
        }
