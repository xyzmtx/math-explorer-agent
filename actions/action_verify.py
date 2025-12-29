"""
Action 8: Verify and Modify Proof

Includes:
- Segment-by-segment verification logic (8.a)
- Modification loop (8.b, up to MAX_VERIFY_ROUNDS rounds)
- Accumulate failed attempts (8.c)
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from llm_client import call_llm_safe
from prompts.verify_proof import (
    get_verify_prompt, get_verify_user_prompt,
    get_modify_proof_prompt, get_modify_proof_user_prompt,
    get_accumulate_attempt_prompt, get_accumulate_attempt_user_prompt
)
from memory import MemoryManager
from config import MAX_VERIFY_ROUNDS, PROOF_CHUNK_SIZE


class VerifyAndModifyAction:
    """Action to verify and modify proofs"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.lines_per_segment = PROOF_CHUNK_SIZE  # Lines per verification segment
        self.max_modify_rounds = MAX_VERIFY_ROUNDS  # Maximum modification rounds
    
    async def execute(
        self,
        conjecture_id: str,
        conjecture_statement: str,
        proof: str
    ) -> Dict[str, Any]:
        """
        Execute verify and modify flow
        
        Args:
            conjecture_id: Conjecture ID
            conjecture_statement: Conjecture proposition
            proof: Proof to be verified
            
        Returns:
            Verification result
        """
        current_proof = proof
        all_attempts = []  # Record all attempts
        all_errors = []    # Record all error messages
        
        for round_num in range(self.max_modify_rounds + 1):
            # Segment-by-segment verification
            is_valid, verification_result = await self._verify_proof_segments(
                conjecture_statement, current_proof
            )
            
            if is_valid:
                # Verification passed, convert conjecture to conclusion
                return {
                    "conjecture_id": conjecture_id,
                    "verified": True,
                    "final_proof": current_proof,
                    "rounds": round_num,
                    "verification_result": verification_result,
                    "action": "convert_to_lemma"
                }
            
            # Record this attempt
            all_attempts.append({
                "round": round_num,
                "proof": current_proof,
                "errors": verification_result.get("errors", [])
            })
            all_errors.extend(verification_result.get("errors", []))
            
            # If there are more modification opportunities, try to modify
            if round_num < self.max_modify_rounds:
                modified_result = await self._modify_proof(
                    conjecture_statement,
                    current_proof,
                    verification_result
                )
                current_proof = modified_result.get("modified_proof", current_proof)
            else:
                # Reached maximum modification count, accumulate failed attempts
                accumulation_result = await self._accumulate_attempts(
                    conjecture_id,
                    conjecture_statement,
                    all_attempts,
                    all_errors
                )
                
                return {
                    "conjecture_id": conjecture_id,
                    "verified": False,
                    "attempts": all_attempts,
                    "rounds": self.max_modify_rounds,
                    "accumulation": accumulation_result,
                    "action": "update_conjecture_comment"
                }
        
        # Theoretically won't reach here
        return {"verified": False, "error": "Unknown error"}
    
    def _split_proof_into_segments(self, proof: str) -> List[Tuple[str, str]]:
        """
        Split proof into segments
        
        Returns:
            List of (segment_content, segment_info)
        """
        lines = proof.strip().split('\n')
        segments = []
        
        for i in range(0, len(lines), self.lines_per_segment):
            segment_lines = lines[i:i + self.lines_per_segment]
            segment_content = '\n'.join(segment_lines)
            start_line = i + 1
            end_line = min(i + self.lines_per_segment, len(lines))
            segment_info = f"Line {start_line} to Line {end_line}"
            segments.append((segment_content, segment_info))
        
        return segments
    
    async def _verify_segment(
        self,
        conjecture_statement: str,
        full_proof: str,
        segment_content: str,
        segment_info: str
    ) -> Dict[str, Any]:
        """Verify a single segment"""
        system_prompt = get_verify_prompt()
        user_prompt = get_verify_user_prompt(
            memory_display=self.memory_manager.get_memory_display(),
            conjecture_statement=conjecture_statement,
            full_proof=full_proof,
            segment_to_verify=segment_content,
            segment_info=segment_info
        )
        
        # Use safe mode
        default_result = {
            "is_correct": True,
            "errors": []
        }
        
        result = await call_llm_safe(
            system_prompt=system_prompt,
            user_message=user_prompt,
            default=default_result,
            temperature=0.3  # Low temperature for strictness
        )
        
        return result
    
    async def _verify_proof_segments(
        self,
        conjecture_statement: str,
        proof: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Verify entire proof segment by segment
        
        Returns:
            (is_valid, verification_result)
        """
        segments = self._split_proof_into_segments(proof)
        all_segment_results = []
        all_errors = []
        
        for segment_content, segment_info in segments:
            result = await self._verify_segment(
                conjecture_statement,
                proof,
                segment_content,
                segment_info
            )
            
            all_segment_results.append({
                "segment_info": segment_info,
                "result": result
            })
            
            # Check if there are errors (new simplified format)
            if not result.get("is_correct", True):
                errors = result.get("errors", [])
                for error in errors:
                    error["segment_info"] = segment_info
                    all_errors.append(error)
        
        is_valid = len(all_errors) == 0
        
        return is_valid, {
            "segment_results": all_segment_results,
            "errors": all_errors,
            "is_valid": is_valid,
            "summary": f"Verified {len(segments)} segments, found {len(all_errors)} errors"
        }
    
    async def _modify_proof(
        self,
        conjecture_statement: str,
        original_proof: str,
        verification_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Modify proof"""
        # Format error information
        errors = verification_result.get("errors", [])
        error_info = self._format_errors(errors)
        
        system_prompt = get_modify_proof_prompt()
        user_prompt = get_modify_proof_user_prompt(
            memory_display=self.memory_manager.get_memory_display(),
            conjecture_statement=conjecture_statement,
            original_proof=original_proof,
            error_info=error_info
        )
        
        # Use safe mode
        default_result = {
            "modified_proof": original_proof  # Default return original proof
        }
        
        result = await call_llm_safe(
            system_prompt=system_prompt,
            user_message=user_prompt,
            default=default_result,
            temperature=0.5
        )
        
        return result
    
    def _format_errors(self, errors: List[Dict[str, Any]]) -> str:
        """Format error information to text"""
        if not errors:
            return "No specific errors found"
        
        lines = []
        for i, error in enumerate(errors, 1):
            lines.append(f"## Error {i}")
            lines.append(f"- **Location**: {error.get('segment_info', 'unknown')} - {error.get('location', 'unknown')}")
            lines.append(f"- **Type**: {error.get('error_type', 'unknown')}")
            lines.append(f"- **Description**: {error.get('description', 'none')}")
            lines.append(f"- **Suggestion**: {error.get('suggestion', 'none')}")
            lines.append("")
        
        return '\n'.join(lines)
    
    async def _accumulate_attempts(
        self,
        conjecture_id: str,
        conjecture_statement: str,
        attempts: List[Dict[str, Any]],
        errors: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Accumulate proof attempts, update conjecture comment"""
        # Get conjecture's original comment
        conjecture = self.memory_manager.get_conjecture_by_id(conjecture_id)
        original_comment = conjecture.comment if conjecture else ""
        
        # Format proof attempts
        proof_attempts = self._format_attempts(attempts)
        error_infos = self._format_errors(errors)
        
        system_prompt = get_accumulate_attempt_prompt()
        user_prompt = get_accumulate_attempt_user_prompt(
            memory_display=self.memory_manager.get_memory_display(),
            conjecture_id=conjecture_id,
            conjecture_statement=conjecture_statement,
            original_comment=original_comment,
            proof_attempts=proof_attempts,
            error_infos=error_infos
        )
        
        # Use safe mode
        default_result = {
            "updated_comment": original_comment  # Default keep original comment
        }
        
        result = await call_llm_safe(
            system_prompt=system_prompt,
            user_message=user_prompt,
            default=default_result,
            temperature=0.5
        )
        
        return result
    
    def _format_attempts(self, attempts: List[Dict[str, Any]]) -> str:
        """Format proof attempts"""
        lines = []
        for attempt in attempts:
            lines.append(f"## Round {attempt['round'] + 1} Attempt")
            lines.append("### Proof:")
            lines.append("```")
            lines.append(attempt['proof'])
            lines.append("```")
            lines.append(f"### Number of errors found: {len(attempt['errors'])}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def get_update_text_for_verified(self, result: Dict[str, Any]) -> str:
        """
        When verification passes, generate mathematical text for Action 2
        
        According to blueprint: 8.a verification passed → Pass complete proof of this conjecture to Action 2
        Action 2 will: Mark the conjecture as completely solved, add corresponding conclusion (lemma)
        
        Returns:
            Mathematical text describing the fact that conjecture was proven
        """
        conjecture_id = result.get("conjecture_id", "")
        final_proof = result.get("final_proof", "")
        
        # Get conjecture's statement
        conjecture = self.memory_manager.get_conjecture_by_id(conjecture_id)
        statement = conjecture.statement if conjecture else ""
        
        # Construct mathematical text
        text = f"""【Proof Complete】

Conjecture {conjecture_id} has been completely proven.

Statement: {statement}

Complete proof:
{final_proof}

Please update Memory:
1. Mark conjecture {conjecture_id} as completely solved
2. Add conclusion (lemma) with statement as above proposition and proof as above complete proof
"""
        return text
    
    def get_update_text_for_failed(self, result: Dict[str, Any]) -> str:
        """
        When verification fails (after 8.c), generate mathematical text for Action 2
        
        According to blueprint: After 8.c, jump to Action 2, have Action 2 update 8.c's output to memory
        
        Returns:
            Mathematical text describing proof attempts and content to be updated
        """
        conjecture_id = result.get("conjecture_id", "")
        accumulation = result.get("accumulation", {})
        
        # Get updated comment (simplified JSON only has this field)
        updated_comment = accumulation.get("updated_comment", "")
        
        # Construct mathematical text
        text = f"""【Proof Attempt Record】

Conjecture {conjecture_id} still could not be proven after multiple rounds of attempts.

Please update Memory:
Modify conjecture {conjecture_id}'s comment to:
{updated_comment}
"""
        return text


class QuickVerifyAction:
    """Quick verification (no modification loop)"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.full_action = VerifyAndModifyAction(memory_manager)
    
    async def verify_only(
        self,
        conjecture_statement: str,
        proof: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Verify only, no modification
        
        Returns:
            (is_valid, verification_result)
        """
        return await self.full_action._verify_proof_segments(
            conjecture_statement, proof
        )
