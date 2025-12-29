"""
Action 7: Attempt to solve a mathematical conjecture

Flow:
- 7.a Input Memory + conjecture → Output mathematical text
- If text starts with "【Proof Complete】" or "【Disproof Complete】" → Extract proof → Jump to Action 8 verify & modify
- Otherwise → Jump to Action 2 to update memory (update by-products)
"""

from typing import Dict, Any, Tuple
from llm_client import call_llm
from prompts.solve_conjecture import get_solve_conjecture_prompt, get_solve_conjecture_user_prompt
from memory import MemoryManager


class SolveConjectureAction:
    """Action to solve mathematical conjectures"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
    
    async def execute(self, conjecture_id: str) -> Dict[str, Any]:
        """
        Execute solve conjecture action (Action 7.a)
        
        Input: Memory + one conjecture
        Output: Mathematical text (starts with "【Proof Complete】" or "【Disproof Complete】" when completely solved)
        
        Args:
            conjecture_id: ID of the conjecture to solve
            
        Returns:
            Result containing mathematical text
        """
        # Get conjecture info
        conjecture = self.memory_manager.get_conjecture_by_id(conjecture_id)
        if not conjecture:
            return {
                "error": f"Conjecture not found: {conjecture_id}",
                "math_text": "",
                "solved": False,
                "action": "solve_conjecture"
            }
        
        system_prompt = get_solve_conjecture_prompt()
        user_prompt = get_solve_conjecture_user_prompt(
            memory_display=self.memory_manager.get_memory_display(),
            conjecture_id=conjecture_id,
            conjecture_statement=conjecture.statement,
            conjecture_comment=conjecture.comment
        )
        
        # Call LLM, get natural language output directly
        math_text = await call_llm(
            system_prompt=system_prompt,
            user_message=user_prompt,
            temperature=0.5
        )
        
        # Detect if completely solved
        text_stripped = math_text.strip()
        solved = text_stripped.startswith("【Proof Complete】") or text_stripped.startswith("【证明完成】")
        disproven = text_stripped.startswith("【Disproof Complete】") or text_stripped.startswith("【证伪完成】")
        
        # According to blueprint: both proof complete and disproof complete should enter verification flow
        needs_verification = solved or disproven
        
        return {
            "conjecture_id": conjecture_id,
            "conjecture_statement": conjecture.statement,
            "math_text": math_text,
            "solved": solved,
            "disproven": disproven,
            "needs_verification": needs_verification,  # Both proof and disproof need verification
            "action": "solve_conjecture"
        }
    
    def extract_proof(self, result: Dict[str, Any]) -> Tuple[str, str]:
        """
        Extract proof from result, to be passed to Action 8 for verification
        
        When conjecture is completely solved (starts with "【Proof Complete】" or "【Disproof Complete】"), extract proof
        
        Returns:
            (conjecture_statement, proof)
        """
        math_text = result.get("math_text", "")
        statement = result.get("conjecture_statement", "")
        
        text_stripped = math_text.strip()
        
        # Remove marker, the rest is proof
        if text_stripped.startswith("【Proof Complete】"):
            proof = text_stripped[len("【Proof Complete】"):].strip()
        elif text_stripped.startswith("【证明完成】"):
            proof = text_stripped[len("【证明完成】"):].strip()
        elif text_stripped.startswith("【Disproof Complete】"):
            proof = text_stripped[len("【Disproof Complete】"):].strip()
        elif text_stripped.startswith("【证伪完成】"):
            proof = text_stripped[len("【证伪完成】"):].strip()
        else:
            proof = math_text
        
        return (statement, proof)
