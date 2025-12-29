"""
Math Explorer Agent Main Module

Responsible for:
- Initializing all components
- Executing actions and updating Memory
- Coordinating parallel tasks
- Providing human intervention interface
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import json
import os

from memory import MemoryManager
from coordinator import Coordinator, InitialCoordinator, ActionRecord, ActionStatus
from actions.action_parse import ParseAction
from actions.action_update import UpdateMemoryAction
from actions.action_retrieval import RetrievalAction
from actions.action_propose_objects import ProposeObjectsAction
from actions.action_propose_directions import ProposeDirectionsAction
from actions.action_explore import ExploreDirectionAction
from actions.action_solve import SolveConjectureAction
from actions.action_verify import VerifyAndModifyAction
from config import MEMORY_SAVE_PATH


class MathExplorerAgent:
    """Math Explorer Agent"""
    
    def __init__(
        self,
        save_path: str = MEMORY_SAVE_PATH,
        auto_save: bool = True
    ):
        """
        Initialize Agent
        
        Args:
            save_path: Memory save path
            auto_save: Whether to auto-save Memory
        """
        # Initialize Memory manager
        self.memory_manager = MemoryManager(save_path=save_path)
        
        # Initialize coordinator
        self.coordinator = Coordinator(self.memory_manager)
        
        # Initialize all actions
        self.actions = {
            "parse": ParseAction(self.memory_manager),
            "update": UpdateMemoryAction(self.memory_manager),
            "retrieval": RetrievalAction(self.memory_manager),
            "propose_objects": ProposeObjectsAction(self.memory_manager),
            "propose_directions": ProposeDirectionsAction(self.memory_manager),
            "explore_direction": ExploreDirectionAction(self.memory_manager),
            "solve_conjecture": SolveConjectureAction(self.memory_manager),
            "verify": VerifyAndModifyAction(self.memory_manager)
        }
        
        self.auto_save = auto_save
        self._is_running = False
        self._should_stop = False
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._human_intervention_pending = False
        self._human_response: Optional[str] = None
        
        # Memory update lock - ensures only one action chain can execute action 2 (update_memory) at a time
        self._memory_update_lock = asyncio.Lock()
    
    # ==================== Event Handling ====================
    
    def on(self, event: str, handler: Callable):
        """Register event handler"""
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)
    
    def _emit(self, event: str, data: Any = None):
        """Trigger event"""
        handlers = self._event_handlers.get(event, [])
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                print(f"Event handler error: {e}")
    
    # ==================== Initialization Flow ====================
    
    async def initialize_from_input(self, raw_input: str) -> Dict[str, Any]:
        """
        Initialize from raw input
        
        Args:
            raw_input: Raw mathematical text
            
        Returns:
            Parse result
        """
        self._emit("status", "Parsing input...")
        
        # Parse raw input
        parse_result = await self.actions["parse"].execute(raw_input)
        
        # Save Memory
        if self.auto_save:
            filepath = self._save_memory("initial")
            self._emit("memory_saved", filepath)  # Send directly during initialization, not through buffer
        
        self._emit("memory_updated", {"source": "parse_input", "has_update": True})
        self._emit("status", "Initialization complete")
        
        return parse_result
    
    async def load_from_file(self, filepath: str) -> bool:
        """Load Memory from file"""
        success = self.memory_manager.load(filepath)
        if success:
            self._emit("memory_updated", {"source": "load_file", "has_update": True})
            self._emit("status", f"Loaded Memory: {filepath}")
        return success
    
    # ==================== Action Execution ====================
    
    async def execute_action(self, record: ActionRecord) -> Dict[str, Any]:
        """
        Execute single action
        
        Args:
            record: Action record
            
        Returns:
            Execution result
        """
        action_type = record.action_type
        action_id = record.id
        params = record.params
        
        self._emit("action_start", {
            "action_id": action_id,
            "action_type": action_type,
            "params": params
        })
        
        try:
            self.coordinator.start_action(action_id)
            
            # All execute methods receive action_id for proper log buffering
            if action_type == "retrieval":
                result = await self._execute_retrieval(action_id)
            elif action_type == "propose_objects":
                result = await self._execute_propose_objects(action_id)
            elif action_type == "propose_directions":
                result = await self._execute_propose_directions(action_id)
            elif action_type == "explore_direction":
                result = await self._execute_explore_direction(action_id, params.get("direction_id"))
            elif action_type == "solve_conjecture":
                result = await self._execute_solve_conjecture(action_id, params.get("conjecture_id"))
            elif action_type == "verify":
                result = await self._execute_verify(
                    action_id,
                    params.get("conjecture_id"),
                    params.get("conjecture_statement"),
                    params.get("proof")
                )
            else:
                result = {"error": f"Unknown action type: {action_type}"}
            
            self.coordinator.complete_action(action_id, result)
            
            self._emit("action_complete", {
                "action_id": action_id,
                "result": result
            })
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            self.coordinator.fail_action(action_id, error_msg)
            
            self._emit("action_error", {
                "action_id": action_id,
                "error": error_msg
            })
            
            return {"error": error_msg}
    
    def _emit_action(self, action_id: str, event: str, data: Any):
        """Send event with action_id"""
        if isinstance(data, dict):
            data["_action_id"] = action_id
        else:
            data = {"_action_id": action_id, "data": data}
        self._emit(event, data)
    
    async def _update_memory_with_text(
        self,
        action_id: str,
        math_text: str,
        source: str
    ) -> Dict[str, Any]:
        """
        Memory update operation with lock (Action 2) - receives mathematical text
        
        Strictly follows blueprint: Action 2 receives mathematical text, outputs update instructions
        
        Args:
            action_id: Current action ID
            math_text: Mathematical text (output from other actions)
            source: Update source
            
        Returns:
            Action 2 execution result
        """
        if not math_text or not math_text.strip():
            self._emit_action(action_id, "action_chain", {"step": "2.Update Memory", "status": "No content to update"})
            return {"updates_applied": [], "summary": "No updates"}
        
        # Send waiting for lock status
        self._emit_action(action_id, "action_chain", {"step": "2.Update Memory", "status": "Waiting for Memory lock..."})
        
        async with self._memory_update_lock:
            # Execute update after acquiring lock
            self._emit_action(action_id, "action_chain", {"step": "2.Update Memory", "status": "Lock acquired, calling Action 2 to process mathematical text..."})
            
            # Call Action 2's execute method (receives mathematical text, calls LLM to generate update instructions)
            result = await self.actions["update"].execute(math_text)
            
            updates_applied = result.get("updates_applied", [])
            has_update = len(updates_applied) > 0
            
            if has_update:
                self._emit_action(action_id, "action_chain", {"step": "2.Update Memory", "status": f"Applied {len(updates_applied)} updates"})
            else:
                self._emit_action(action_id, "action_chain", {"step": "2.Update Memory", "status": "No new content to update"})
            
            self._emit_action(action_id, "memory_updated", {"source": source, "has_update": has_update})
            
            if self.auto_save and has_update:
                filepath = self._save_memory(source)
                self._emit_action(action_id, "memory_saved", {"path": filepath})
        
        return result
    
    async def _execute_retrieval(self, action_id: str) -> Dict[str, Any]:
        """
        Execute retrieval action
        
        Flow (strictly follows blueprint):
        - Action 3.a: Input Memory → Output mathematical text
        - Jump to Action 2: Input mathematical text → Update Memory
        """
        self._emit_action(action_id, "action_chain", {"step": "3.Retrieval", "status": "Starting to retrieve related theories"})
        
        # Action 3.a: Input Memory, output mathematical text
        result = await self.actions["retrieval"].execute()
        
        # Jump to Action 2: Input mathematical text, update Memory
        math_text = result.get("math_text", "")
        await self._update_memory_with_text(action_id, math_text, "retrieval")
        
        return result
    
    async def _execute_propose_objects(self, action_id: str) -> Dict[str, Any]:
        """
        Execute propose objects action
        
        Flow (strictly follows blueprint):
        - Action 4.a: Input Memory → Output mathematical text
        - Jump to Action 2: Input mathematical text → Update Memory
        """
        self._emit_action(action_id, "action_chain", {"step": "4.Propose Objects", "status": "Proposing new mathematical objects and concepts"})
        
        # Action 4.a: Input Memory, output mathematical text
        result = await self.actions["propose_objects"].execute()
        
        # Jump to Action 2: Input mathematical text, update Memory
        math_text = result.get("math_text", "")
        await self._update_memory_with_text(action_id, math_text, "propose_objects")
        
        return result
    
    async def _execute_propose_directions(self, action_id: str) -> Dict[str, Any]:
        """
        Execute propose directions action
        
        Flow (strictly follows blueprint):
        - Action 5.a: Input Memory → Output mathematical text
        - Jump to Action 2: Input mathematical text → Update Memory
        """
        self._emit_action(action_id, "action_chain", {"step": "5.Propose Directions", "status": "Proposing new exploration directions"})
        
        # Action 5.a: Input Memory, output mathematical text
        result = await self.actions["propose_directions"].execute()
        
        # Jump to Action 2: Input mathematical text, update Memory
        math_text = result.get("math_text", "")
        await self._update_memory_with_text(action_id, math_text, "propose_directions")
        
        return result
    
    async def _execute_explore_direction(self, action_id: str, direction_id: str) -> Dict[str, Any]:
        """
        Execute explore direction action
        
        Flow (strictly follows blueprint):
        - Action 6.a: Input Memory + direction → Output mathematical text
        - Jump to Action 2: Input mathematical text → Update Memory
        """
        self._emit_action(action_id, "action_chain", {"step": "6.Explore Direction", "status": f"Exploring direction {direction_id}"})
        
        # Action 6.a: Input Memory + direction, output mathematical text
        result = await self.actions["explore_direction"].execute(direction_id)
        
        # Jump to Action 2: Input mathematical text, update Memory
        math_text = result.get("math_text", "")
        await self._update_memory_with_text(action_id, math_text, "explore_direction")
        
        return result
    
    async def _execute_solve_conjecture(self, action_id: str, conjecture_id: str) -> Dict[str, Any]:
        """
        Execute solve conjecture action
        
        Flow (strictly follows blueprint):
        - Action 7.a: Input Memory + conjecture → Output mathematical text
        - If starts with "【Proof Complete】" → Extract proof → Jump to Action 8 verify & modify
        - Otherwise → Jump to Action 2 to update memory (update by-products)
        """
        self._emit_action(action_id, "action_chain", {"step": "7.Solve Conjecture", "status": f"Attempting to solve conjecture {conjecture_id}"})
        
        # Action 7.a: Input Memory + conjecture, output mathematical text
        result = await self.actions["solve_conjecture"].execute(conjecture_id)
        
        if result.get("needs_verification"):
            # Completely solved (starts with "【Proof Complete】") → Jump to Action 8 verify & modify
            self._emit_action(action_id, "action_chain", {"step": "→Action 8", "status": "Conjecture solved, entering verification flow"})
            
            statement, proof = self.actions["solve_conjecture"].extract_proof(result)
            
            verify_result = await self._execute_verify_chain(
                action_id=action_id,
                conjecture_id=conjecture_id,
                conjecture_statement=statement,
                proof=proof
            )
            
            result["verify_result"] = verify_result
        else:
            # Not completely solved → Jump to Action 2 to update memory (update by-products)
            math_text = result.get("math_text", "")
            await self._update_memory_with_text(action_id, math_text, "solve_partial")
        
        return result
    
    async def _execute_verify_chain(
        self,
        action_id: str,
        conjecture_id: str,
        conjecture_statement: str,
        proof: str
    ) -> Dict[str, Any]:
        """
        Execute complete verify & modify flow (Action 8)
        
        Flow (strictly follows blueprint):
        - 8.a Verify → Pass → Pass complete proof to Action 2 → Action 2 updates Memory
        - 8.a Verify → Fail → 8.b Modify → 8.a (loop up to 3 times)
        - After 3 times still fail → 8.c Accumulate attempts → Jump to Action 2 → Action 2 updates Memory
        """
        verify_action = self.actions["verify"]
        
        self._emit_action(action_id, "action_chain", {"step": "8.Verify Proof", "status": "Starting segment-by-segment verification..."})
        
        # Execute verify and modify flow (internally contains up to 3 rounds of modification loop)
        result = await verify_action.execute(
            conjecture_id, conjecture_statement, proof
        )
        
        # Generate mathematical text based on verification result, pass to Action 2
        if result.get("verified"):
            # 8.a verification passed → Pass complete proof to Action 2
            self._emit_action(action_id, "action_chain", {"step": "→Action 2", "status": "Verification passed, passing complete proof to Action 2..."})
            update_text = verify_action.get_update_text_for_verified(result)
        else:
            # After 8.c → Jump to Action 2
            self._emit_action(action_id, "action_chain", {"step": "8.c Accumulate Attempts", "status": f"Verification failed ({result.get('rounds', 0)} rounds), organizing proof attempts..."})
            update_text = verify_action.get_update_text_for_failed(result)
        
        # Jump to Action 2: update_memory (with lock)
        self._emit_action(action_id, "action_chain", {"step": "2.Update Memory", "status": "Waiting for Memory lock..."})
        
        async with self._memory_update_lock:
            self._emit_action(action_id, "action_chain", {"step": "2.Update Memory", "status": "Lock acquired, calling Action 2..."})
            
            # Call Action 2 to process mathematical text
            update_result = await self.actions["update"].execute(update_text)
            result["update_result"] = update_result
            
            if result.get("verified"):
                self._emit_action(action_id, "action_chain", {"step": "2.Update Memory", "status": f"Verification passed, conjecture {conjecture_id} converted to conclusion"})
            else:
                self._emit_action(action_id, "action_chain", {"step": "2.Update Memory", "status": f"Verification failed, updated comment for conjecture {conjecture_id}"})
            
            self._emit_action(action_id, "memory_updated", {"source": "verify", "verified": result.get("verified", False)})
            
            if self.auto_save:
                filepath = self._save_memory("verify")
                self._emit_action(action_id, "memory_saved", {"path": filepath})
        
        return result
    
    async def _execute_verify(
        self,
        action_id: str,
        conjecture_id: str,
        conjecture_statement: str,
        proof: str
    ) -> Dict[str, Any]:
        """
        Execute verify action (for external calls, such as manually adding verification tasks)
        """
        return await self._execute_verify_chain(
            action_id, conjecture_id, conjecture_statement, proof
        )
    
    # ==================== Main Run Loop ====================
    
    async def run(self, max_rounds: int = 100, rounds_per_checkpoint: int = 10) -> Dict[str, Any]:
        """
        Run Agent main loop
        
        Parallel mechanism:
        - Each round, coordinator decides to execute several actions in parallel (≤10)
        - Execute all actions in parallel, wait for all to complete
        - After all complete, call coordinator to start next round
        
        Human checkpoint mechanism:
        - After running rounds_per_checkpoint rounds, ask user whether to continue
        - User can choose to continue running specified rounds or stop
        
        Args:
            max_rounds: Maximum rounds
            rounds_per_checkpoint: How many rounds before asking user
            
        Returns:
            Run result summary
        """
        self._is_running = True
        self._should_stop = False
        round_num = 0  # Current round number
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info("[Agent.run] Starting exploration loop")
        
        self._emit("status", "Starting run...")
        
        while self._is_running and round_num < max_rounds:
            round_num += 1
            logger.info(f"[Agent.run] === Round {round_num} starting ===")
            
            # Check if should stop
            if self._should_stop:
                self._emit("status", "User requested stop")
                break
            
            # Check if there's human intervention
            if self._human_intervention_pending:
                await self._wait_for_human_response()
                continue
            
            # Call coordinator to decide this round's actions
            self._emit("status", f"Round {round_num}: Coordinator deciding...")
            logger.info(f"[Agent.run] Round {round_num}: Calling coordinator.decide_next_actions()...")
            decision = await self.coordinator.decide_next_actions()
            logger.info(f"[Agent.run] Round {round_num}: Coordinator decision received: {list(decision.keys())}")
            
            # Coordinator no longer makes stop decisions, skip stop check
            # Stop is controlled by human at checkpoints
            
            # Get new actions
            new_actions = decision.get("new_actions", [])
            if not new_actions:
                self._emit("status", "Coordinator assigned no new actions, exploration complete")
                break
            
            # Add actions to queue
            action_records = []
            for action_data in new_actions:
                record = self.coordinator.add_action_from_decision(action_data)
                if record:
                    action_records.append(record)
            
            if not action_records:
                self._emit("status", "No valid actions to execute, exploration complete")
                break
            
            # Display actions to execute this round
            self._emit("round_start", {
                "round": round_num,
                "actions": [{"id": r.id, "type": r.action_type, "reason": r.reason} for r in action_records]
            })
            
            # Mark all actions as started
            for record in action_records:
                self.coordinator.start_action(record.id)
            
            # Execute all actions in parallel this round
            self._emit("status", f"Round {round_num}: Executing {len(action_records)} actions in parallel...")
            tasks = [self.execute_action(record) for record in action_records]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Summarize this round's results
            success_count = sum(1 for r in results if not isinstance(r, Exception))
            fail_count = len(results) - success_count
            
            self._emit("round_complete", {
                "round": round_num,
                "success": success_count,
                "failed": fail_count,
                "status": self.coordinator.get_status_summary()
            })
            
            # Check if reached checkpoint (human intervention point)
            if rounds_per_checkpoint > 0 and round_num % rounds_per_checkpoint == 0:
                # Set pending flag BEFORE emitting event, so event handler can clear it
                self._human_intervention_pending = True
                self._human_response = None
                
                self._emit("checkpoint_reached", {
                    "round": round_num,
                    "max_rounds": max_rounds,
                    "memory_summary": self.memory_manager.get_memory_summary(),
                    "status": self.coordinator.get_status_summary()
                })
                
                # Wait for human response (if handler hasn't already provided it)
                await self._wait_for_human_response()
                
                # Process user response
                if self._human_response == "stop" or self._human_response == "0":
                    self._emit("status", "User decided to stop exploration")
                    break
                elif self._human_response and self._human_response.isdigit():
                    # User specified number of rounds to continue
                    additional_rounds = int(self._human_response)
                    max_rounds = round_num + additional_rounds
                    self._emit("status", f"Continuing for {additional_rounds} rounds, new max rounds: {max_rounds}")
                else:
                    # Default continue remaining rounds
                    self._emit("status", "Continuing exploration...")
        
        self._is_running = False
        
        # Save final Memory
        filepath = self._save_memory("final")
        self._emit("memory_saved", filepath)  # Send directly, not through buffer
        
        return {
            "rounds": round_num,
            "final_memory": self.memory_manager.get_memory_summary(),
            "action_log": self.coordinator.action_log.to_display_string()
        }
    
    async def _run_coordinator(self) -> bool:
        """
        Run coordinator decision
        
        Returns:
            bool: True means continue, False means stop
        """
        self._emit("status", "Coordinator deciding...")
        
        decision = await self.coordinator.decide_next_actions()
        
        # Handle suggestions
        suggestions = self.coordinator.get_suggestions(decision)
        if suggestions:
            self._emit("suggestion", suggestions)
            # Can request human intervention here
            # self._request_human_intervention(suggestions)
        
        # Check if decided to stop
        decision_type = decision.get("decision", {}).get("type", "")
        if decision_type == "stop":
            self._emit("status", "Coordinator decided to end exploration")
            return False
        
        # Add new actions
        new_records = self.coordinator.process_decision(decision)
        
        if new_records:
            self._emit("new_actions", [
                {"id": r.id, "type": r.action_type, "reason": r.reason}
                for r in new_records
            ])
        
        return True
    
    # ==================== Human Intervention ====================
    
    def request_stop(self):
        """Request to stop Agent"""
        self._should_stop = True
        self._emit("status", "Stopping...")
    
    def _request_human_intervention(self, reason: str):
        """Request human intervention"""
        self._human_intervention_pending = True
        self._emit("human_intervention_requested", reason)
    
    async def _wait_for_human_response(self):
        """Wait for human response"""
        while self._human_intervention_pending and not self._should_stop:
            await asyncio.sleep(0.5)
    
    def provide_human_response(self, response: str):
        """Provide human response"""
        self._human_response = response
        self._human_intervention_pending = False
    
    def add_manual_action(
        self,
        action_type: str,
        params: Dict[str, Any] = None,
        reason: str = "Manually added"
    ):
        """Manually add action"""
        self.coordinator.add_action_from_decision({
            "action_type": action_type,
            "params": params or {},
            "priority": "high",
            "reason": reason
        })
        self._emit("action_added", {
            "action_type": action_type,
            "params": params,
            "reason": reason
        })
    
    def add_manual_text(self, text: str):
        """
        Manually add mathematical text to Memory
        
        This will trigger update action
        """
        asyncio.create_task(self._add_text_async(text))
    
    async def _add_text_async(self, text: str):
        """Asynchronously add text"""
        await self.actions["update"].execute(text)
        if self.auto_save:
            filepath = self._save_memory("manual_add")
            self._emit("memory_saved", filepath)
        self._emit("memory_updated", {"source": "manual_add", "has_update": True})
    
    # ==================== Memory Operations ====================
    
    def _save_memory(self, tag: str = "") -> str:
        """
        Save Memory
        
        Returns:
            Saved file path
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"memory_{tag}_{timestamp}.json" if tag else f"memory_{timestamp}.json"
        filepath = self.memory_manager.save(filename)
        # Note: Do not send memory_saved event here, let caller decide
        return filepath
    
    def get_memory_display(self) -> str:
        """Get Memory display content"""
        return self.memory_manager.get_memory_display()
    
    def get_memory_summary(self) -> str:
        """Get Memory summary"""
        return self.memory_manager.get_memory_summary()
    
    def export_memory(self, filepath: str):
        """Export Memory to specified path"""
        self.memory_manager.save(filepath)
    
    # ==================== Status Query ====================
    
    def is_running(self) -> bool:
        """Check if Agent is running"""
        return self._is_running
    
    def get_action_log(self) -> str:
        """Get action log"""
        return self.coordinator.action_log.to_display_string()
    
    def get_status(self) -> str:
        """Get current status"""
        return self.coordinator.get_status_summary()
