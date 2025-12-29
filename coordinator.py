"""
Coordinator Module

Responsible for:
- Analyzing Memory state
- Deciding next actions
- Controlling parallel action count
"""

import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from llm_client import call_llm
from prompts.coordinator import get_coordinator_prompt, get_coordinator_user_prompt
from memory import MemoryManager


class ActionStatus(Enum):
    """Action Status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ActionType(Enum):
    """Action Type"""
    PARSE = "parse"
    UPDATE = "update"
    RETRIEVAL = "retrieval"
    PROPOSE_OBJECTS = "propose_objects"
    PROPOSE_DIRECTIONS = "propose_directions"
    EXPLORE_DIRECTION = "explore_direction"
    SOLVE_CONJECTURE = "solve_conjecture"
    VERIFY = "verify"


@dataclass
class ActionRecord:
    """Action Record"""
    id: str
    action_type: str
    params: Dict[str, Any]
    status: ActionStatus
    priority: str
    reason: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class ActionLog:
    """Action Log Manager"""
    records: List[ActionRecord] = field(default_factory=list)
    _action_counter: int = 0
    
    def add_action(
        self,
        action_type: str,
        params: Dict[str, Any],
        priority: str = "medium",
        reason: str = ""
    ) -> ActionRecord:
        """Add new action record"""
        self._action_counter += 1
        record = ActionRecord(
            id=f"action_{self._action_counter:04d}",
            action_type=action_type,
            params=params,
            status=ActionStatus.PENDING,
            priority=priority,
            reason=reason
        )
        self.records.append(record)
        return record
    
    def start_action(self, action_id: str):
        """Mark action as started"""
        for record in self.records:
            if record.id == action_id:
                record.status = ActionStatus.RUNNING
                record.start_time = datetime.now()
                break
    
    def complete_action(self, action_id: str, result: Dict[str, Any]):
        """Mark action as completed"""
        for record in self.records:
            if record.id == action_id:
                record.status = ActionStatus.COMPLETED
                record.end_time = datetime.now()
                record.result = result
                break
    
    def fail_action(self, action_id: str, error: str):
        """Mark action as failed"""
        for record in self.records:
            if record.id == action_id:
                record.status = ActionStatus.FAILED
                record.end_time = datetime.now()
                record.error = error
                break
    
    def get_running_actions(self) -> List[ActionRecord]:
        """Get running actions"""
        return [r for r in self.records if r.status == ActionStatus.RUNNING]
    
    def get_pending_actions(self) -> List[ActionRecord]:
        """Get pending actions"""
        return [r for r in self.records if r.status == ActionStatus.PENDING]
    
    def get_recent_completed(self, n: int = 5) -> List[ActionRecord]:
        """Get recently completed actions"""
        completed = [r for r in self.records if r.status == ActionStatus.COMPLETED]
        return sorted(completed, key=lambda x: x.end_time or datetime.min, reverse=True)[:n]
    
    def to_display_string(self) -> str:
        """Generate log display string"""
        lines = []
        
        # Running actions
        running = self.get_running_actions()
        if running:
            lines.append("## Running Actions")
            for r in running:
                duration = ""
                if r.start_time:
                    duration = f" (running for {(datetime.now() - r.start_time).seconds}s)"
                lines.append(f"- [{r.id}] {r.action_type}({r.params}) - {r.reason}{duration}")
            lines.append("")
        
        # Pending actions
        pending = self.get_pending_actions()
        if pending:
            lines.append("## Pending Actions")
            for r in pending:
                lines.append(f"- [{r.id}] {r.action_type}({r.params}) - Priority: {r.priority}")
            lines.append("")
        
        # Recently completed actions
        recent = self.get_recent_completed(5)
        if recent:
            lines.append("## Recently Completed Actions")
            for r in recent:
                status_str = "✓" if r.status == ActionStatus.COMPLETED else "✗"
                lines.append(f"- {status_str} [{r.id}] {r.action_type}({r.params})")
            lines.append("")
        
        if not lines:
            return "No action records"
        
        return '\n'.join(lines)


class Coordinator:
    """Coordinator"""
    
    MAX_PARALLEL_ACTIONS = 10
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.action_log = ActionLog()
        self._last_memory_version = 0
    
    def should_run(self) -> bool:
        """Check if coordinator should run (only after Memory update)"""
        current_version = self.memory_manager.get_version()
        if current_version > self._last_memory_version:
            self._last_memory_version = current_version
            return True
        return False
    
    async def decide_next_actions(self) -> Dict[str, Any]:
        """
        Decide next actions
        
        Returns:
            {
                "decision": "wait" | "new_actions",
                "actions": [...]  # if new_actions
            }
        """
        from llm_client import call_llm_safe
        
        system_prompt = get_coordinator_prompt()
        user_prompt = get_coordinator_user_prompt(
            memory_display=self.memory_manager.get_memory_display(),
            log_history=self.action_log.to_display_string()
        )
        
        # Use safe mode to call LLM (with more robust defaults)
        default_result = {
            "new_actions": []
        }
        
        try:
            result = await call_llm_safe(
                system_prompt=system_prompt,
                user_message=user_prompt,
                default=default_result,
                temperature=0.3,  # Lower temperature for more stable output
                max_tokens=4096   # Reduce token limit to avoid truncation
            )
            
            # Validate result format
            if not isinstance(result, dict):
                return default_result
            
            # Ensure new_actions field exists
            if "new_actions" not in result:
                result["new_actions"] = []
            
            return result
            
        except Exception as e:
            print(f"[Coordinator] Decision error: {e}")
            return default_result
    
    def can_add_more_actions(self) -> bool:
        """Check if more parallel actions can be added"""
        running = self.action_log.get_running_actions()
        return len(running) < self.MAX_PARALLEL_ACTIONS
    
    def add_action_from_decision(self, action_data: Dict[str, Any]) -> Optional[ActionRecord]:
        """
        Add action from coordinator decision
        
        Args:
            action_data: {
                "action_type": str,
                "params": dict,
                "priority": str
            }
        """
        if not self.can_add_more_actions():
            return None
        
        # Check if conflicts with running actions
        if self._has_conflict(action_data):
            return None
        
        # Auto-generate reason
        action_type = action_data.get("action_type", "")
        params = action_data.get("params", {})
        reason = self._generate_reason(action_type, params)
        
        return self.action_log.add_action(
            action_type=action_type,
            params=params,
            priority=action_data.get("priority", "medium"),
            reason=reason
        )
    
    def _has_conflict(self, action_data: Dict[str, Any]) -> bool:
        """Check if conflicts with running actions"""
        running = self.action_log.get_running_actions()
        action_type = action_data.get("action_type", "")
        params = action_data.get("params", {})
        
        for record in running:
            # Same type and same params conflict
            if record.action_type == action_type and record.params == params:
                return True
            
            # Solve conflict for same conjecture (verify is a follow-up chain of solve, not independent action)
            if action_type == "solve_conjecture":
                target_id = params.get("conjecture_id")
                if record.action_type == "solve_conjecture":
                    if record.params.get("conjecture_id") == target_id:
                        return True
            
            # Explore conflict for same direction
            if action_type == "explore_direction":
                target_id = params.get("direction_id")
                if record.action_type == "explore_direction":
                    if record.params.get("direction_id") == target_id:
                        return True
        
        return False
    
    def _generate_reason(self, action_type: str, params: Dict[str, Any]) -> str:
        """Generate log reason based on action type and params"""
        if action_type == "retrieval":
            return "Retrieve related mathematical theories"
        elif action_type == "propose_objects":
            return "Propose new mathematical objects and concepts"
        elif action_type == "propose_directions":
            return "Propose new exploration directions"
        elif action_type == "explore_direction":
            dir_id = params.get("direction_id", "")
            return f"Explore direction {dir_id}"
        elif action_type == "solve_conjecture":
            conj_id = params.get("conjecture_id", "")
            return f"Attempt to solve conjecture {conj_id}"
        else:
            return action_type
    
    def process_decision(self, decision_result: Dict[str, Any]) -> List[ActionRecord]:
        """
        Process coordinator decision result
        
        Returns:
            List of newly added actions
        """
        new_actions = decision_result.get("new_actions", [])
        if not new_actions:
            return []
        
        added_records = []
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        new_actions.sort(key=lambda x: priority_order.get(x.get("priority", "medium"), 1))
        
        for action_data in new_actions:
            record = self.add_action_from_decision(action_data)
            if record:
                added_records.append(record)
        
        return added_records
    
    def get_next_pending_action(self) -> Optional[ActionRecord]:
        """Get next pending action (by priority)"""
        pending = self.action_log.get_pending_actions()
        if not pending:
            return None
        
        priority_order = {"high": 0, "medium": 1, "low": 2}
        pending.sort(key=lambda x: priority_order.get(x.priority, 1))
        
        return pending[0]
    
    def start_action(self, action_id: str):
        """Start executing action"""
        self.action_log.start_action(action_id)
    
    def complete_action(self, action_id: str, result: Dict[str, Any]):
        """Complete action"""
        self.action_log.complete_action(action_id, result)
    
    def fail_action(self, action_id: str, error: str):
        """Action failed"""
        self.action_log.fail_action(action_id, error)
    
    def get_suggestions(self, decision_result: Dict[str, Any]) -> Optional[str]:
        """Get suggestions for human intervention"""
        return decision_result.get("suggestions")
    
    def get_status_summary(self) -> str:
        """Get current status summary"""
        running = len(self.action_log.get_running_actions())
        pending = len(self.action_log.get_pending_actions())
        completed = len([r for r in self.action_log.records 
                        if r.status == ActionStatus.COMPLETED])
        failed = len([r for r in self.action_log.records 
                     if r.status == ActionStatus.FAILED])
        
        return f"Running: {running} | Pending: {pending} | Completed: {completed} | Failed: {failed}"


class InitialCoordinator:
    """Initial Coordinator (No LLM call needed)"""
    
    @staticmethod
    def get_initial_actions(memory_manager: MemoryManager) -> List[Dict[str, Any]]:
        """
        Get initial action list
        
        Called after Memory is just initialized, returns a set of initial actions
        """
        actions = []
        memory = memory_manager.get_memory()
        
        # If there are exploration directions, add retrieval and explore actions
        if memory.directions:
            actions.append({
                "action_type": "retrieval",
                "params": {},
                "priority": "high",
                "reason": "Retrieve related mathematical theories, establish knowledge base"
            })
            
            # Explore first direction
            first_direction = memory.directions[0]
            actions.append({
                "action_type": "explore_direction",
                "params": {"direction_id": first_direction.id},
                "priority": "high",
                "reason": f"Explore main direction: {first_direction.description[:50]}..."
            })
        
        # If there are high confidence conjectures, add solve action
        high_confidence_conjectures = [
            c for c in memory.conjectures 
            if c.confidence_score.value == "High"
        ]
        if high_confidence_conjectures:
            first_conj = high_confidence_conjectures[0]
            actions.append({
                "action_type": "solve_conjecture",
                "params": {"conjecture_id": first_conj.id},
                "priority": "high",
                "reason": f"Attempt to prove high confidence conjecture: {first_conj.statement[:50]}..."
            })
        
        # If not much content, propose new objects
        if len(memory.objects) < 5 and len(memory.concepts) < 3:
            actions.append({
                "action_type": "propose_objects",
                "params": {},
                "priority": "medium",
                "reason": "Explore possible new mathematical objects and concepts"
            })
        
        return actions
