"""
Math Explorer Agent Entry Point

Provides command line interface and interactive operations
"""

import asyncio
import argparse
import os
import sys
from datetime import datetime
from typing import Optional

from agent import MathExplorerAgent
from config import MEMORY_SAVE_PATH


class AgentCLI:
    """Agent Command Line Interface"""
    
    def __init__(self):
        self.agent: Optional[MathExplorerAgent] = None
        self._setup_colors()
    
    def _setup_colors(self):
        """Setup terminal colors"""
        self.COLORS = {
            "reset": "\033[0m",
            "bold": "\033[1m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "red": "\033[91m",
            "blue": "\033[94m",
            "cyan": "\033[96m",
            "magenta": "\033[95m"
        }
    
    def _color(self, text: str, color: str) -> str:
        """Add color to text"""
        return f"{self.COLORS.get(color, '')}{text}{self.COLORS['reset']}"
    
    def _print_header(self, title: str):
        """Print header"""
        print("\n" + "=" * 60)
        print(self._color(f" {title}", "bold"))
        print("=" * 60)
    
    def _print_status(self, message: str):
        """Print status message"""
        print(self._color(f"[Status] {message}", "cyan"))
    
    def _print_success(self, message: str):
        """Print success message"""
        print(self._color(f"[Success] {message}", "green"))
    
    def _print_error(self, message: str):
        """Print error message"""
        print(self._color(f"[Error] {message}", "red"))
    
    def _print_warning(self, message: str):
        """Print warning message"""
        print(self._color(f"[Warning] {message}", "yellow"))
    
    def _print_action(self, action_type: str, details: str = ""):
        """Print action information"""
        print(self._color(f"[Action] {action_type}", "magenta") + 
              (f" - {details}" if details else ""))
    
    def _setup_event_handlers(self):
        """Setup event handlers"""
        # Log buffer for each action
        self._action_logs = {}  # action_id -> {"type": action_type, "logs": [...]}
        
        self.agent.on("status", lambda msg: self._print_status(msg))
        
        self.agent.on("memory_updated", lambda data: 
            self._buffer_log("memory_update", data))
        
        self.agent.on("memory_saved", lambda path: 
            self._handle_memory_saved(path))
        
        self.agent.on("action_start", lambda data: 
            self._on_action_start(data))
        
        self.agent.on("action_complete", lambda data: 
            self._on_action_complete(data))
        
        self.agent.on("action_error", lambda data: 
            self._on_action_error(data))
        
        self.agent.on("action_chain", lambda data: 
            self._buffer_log("chain", data))
        
        self.agent.on("new_actions", lambda actions: 
            self._print_status(f"Added {len(actions)} new actions"))
        
        self.agent.on("suggestion", lambda msg: 
            self._print_warning(f"Suggestion: {msg}"))
        
        self.agent.on("round_start", lambda data: 
            self._print_round_start(data))
        
        self.agent.on("round_complete", lambda data: 
            self._print_round_complete(data))
        
        self.agent.on("checkpoint_reached", lambda data:
            self._handle_checkpoint(data))
        
        self.agent.on("human_intervention_requested", lambda reason:
            self._handle_human_intervention(reason))
    
    def _on_action_start(self, data: dict):
        """Handle action start - initialize buffer"""
        action_id = data['action_id']
        action_type = data['action_type']
        self._action_logs[action_id] = {
            "type": action_type,
            "logs": []
        }
        # Record start
        self._action_logs[action_id]["logs"].append(
            ("start", f"┌─ Action [{action_id}] {action_type} started")
        )
    
    def _handle_memory_saved(self, path):
        """Handle memory_saved event"""
        # If it's a dict with _action_id, buffer it
        if isinstance(path, dict) and "_action_id" in path:
            self._buffer_log("memory_saved", path)
        else:
            # Otherwise print directly (from initialization and other non-action scenarios)
            self._print_success(f"Memory saved: {path}")
    
    def _buffer_log(self, log_type: str, data):
        """Add log to corresponding action's buffer"""
        # Get action_id from event data
        action_id = None
        if isinstance(data, dict):
            action_id = data.get("_action_id")
        
        if action_id and action_id in self._action_logs:
            self._action_logs[action_id]["logs"].append((log_type, data))
    
    def _on_action_complete(self, data: dict):
        """Handle action complete - output all buffered logs"""
        action_id = data['action_id']
        
        if action_id in self._action_logs:
            logs = self._action_logs[action_id]["logs"]
            
            # Output all buffered logs
            for log_type, log_data in logs:
                if log_type == "start":
                    print(self._color(log_data, "cyan"))
                elif log_type == "chain":
                    step = log_data.get('step', '')
                    status = log_data.get('status', '')
                    print(f"│  → {step}: {status}")
                elif log_type == "memory_update":
                    source = log_data.get('source', 'unknown')
                    has_update = log_data.get('has_update', True)
                    if has_update:
                        print(self._color(f"│  [Memory Updated] Source: {source}", "green"))
                elif log_type == "memory_saved":
                    # log_data is dict containing path and _action_id
                    if isinstance(log_data, dict):
                        path = log_data.get('path', '')
                        if path:
                            print(self._color(f"│  [Saved] {path}", "green"))
            
            # Output completion marker
            print(self._color(f"└─ Action [{action_id}] completed ✓", "green"))
            print()  # Empty line separator
            
            # Clean up buffer
            del self._action_logs[action_id]
    
    def _on_action_error(self, data: dict):
        """Handle action error"""
        action_id = data['action_id']
        error = data.get('error', 'Unknown error')
        
        if action_id in self._action_logs:
            logs = self._action_logs[action_id]["logs"]
            
            # Output all buffered logs
            for log_type, log_data in logs:
                if log_type == "start":
                    print(self._color(log_data, "cyan"))
                elif log_type == "chain":
                    step = log_data.get('step', '')
                    status = log_data.get('status', '')
                    print(f"│  → {step}: {status}")
            
            # Output error
            print(self._color(f"│  [Error] {error}", "red"))
            print(self._color(f"└─ Action [{action_id}] failed ✗", "red"))
            print()
            
            del self._action_logs[action_id]
        else:
            self._print_error(f"Action failed [{action_id}]: {error}")
    
    def _print_round_start(self, data: dict):
        """Print round start info"""
        print(self._color(f"\n{'='*50}", "cyan"))
        print(self._color(f"Round {data['round']} started - Executing {len(data['actions'])} actions", "bold"))
        print(self._color("="*50, "cyan"))
        for action in data['actions']:
            print(f"  • [{action['id']}] {action['type']}: {action['reason'][:50]}...")
    
    def _print_round_complete(self, data: dict):
        """Print round complete info"""
        print(self._color(f"\nRound {data['round']} completed: ", "green") + 
              f"Success {data['success']}, Failed {data['failed']}")
        print(f"  Status: {data['status']}")
    
    def _handle_human_intervention(self, reason: str):
        """Handle human intervention request"""
        self._print_header("Human Intervention Required")
        print(f"Reason: {reason}")
        print("\nOptions:")
        print("  1. Continue running")
        print("  2. Stop Agent")
        print("  3. Manually add action")
        
        choice = input("\nPlease choose (1/2/3): ").strip()
        
        if choice == "2":
            self.agent.request_stop()
        elif choice == "3":
            self._manual_add_action()
        
        self.agent.provide_human_response(choice)
    
    def _handle_checkpoint(self, data: dict):
        """Handle checkpoint reached event - ask user whether to continue"""
        self._print_header(f"Completed {data['round']} rounds of exploration")
        
        print(f"\nCurrent progress summary:")
        print(f"  {data.get('memory_summary', '')[:200]}..." if len(data.get('memory_summary', '')) > 200 else f"  {data.get('memory_summary', '')}")
        print(f"\nAction status: {data.get('status', '')}")
        
        print("\n" + "="*50)
        print("Options:")
        print("  Enter number - Continue running specified rounds")
        print("  Enter 0 or stop - Stop exploration")
        print("  Press Enter - Continue to next checkpoint")
        print("="*50)
        
        while True:
            choice = input("\nEnter number of rounds to continue (or stop to stop): ").strip().lower()
            
            if choice == "stop":
                self.agent.provide_human_response("stop")
                break
            elif choice == "":
                # Press Enter, continue to next checkpoint
                self.agent.provide_human_response("continue")
                break
            elif choice.isdigit():
                self.agent.provide_human_response(choice)
                break
            else:
                print("Invalid input, please enter a number or 'stop'")
    
    def _manual_add_action(self):
        """Manually add action"""
        print("\nAvailable action types:")
        print("  1. retrieval - Retrieve related theories")
        print("  2. propose_objects - Propose new objects/concepts")
        print("  3. propose_directions - Propose new directions")
        print("  4. explore_direction - Explore a direction")
        print("  5. solve_conjecture - Solve a conjecture")
        
        action_map = {
            "1": "retrieval",
            "2": "propose_objects",
            "3": "propose_directions",
            "4": "explore_direction",
            "5": "solve_conjecture"
        }
        
        choice = input("\nChoose action type (1-5): ").strip()
        action_type = action_map.get(choice)
        
        if not action_type:
            self._print_error("Invalid choice")
            return
        
        params = {}
        if action_type == "explore_direction":
            dir_id = input("Enter direction ID (e.g. dir_001): ").strip()
            params["direction_id"] = dir_id
        elif action_type == "solve_conjecture":
            conj_id = input("Enter conjecture ID (e.g. conj_001): ").strip()
            params["conjecture_id"] = conj_id
        
        reason = input("Reason for adding (optional): ").strip() or "Manually added"
        
        self.agent.add_manual_action(action_type, params, reason)
        self._print_success(f"Added action: {action_type}")
    
    async def run_interactive(self):
        """Interactive run"""
        self._print_header("Math Explorer Agent - Interactive Mode")
        
        # Create Agent
        self.agent = MathExplorerAgent()
        self._setup_event_handlers()
        
        # Get initial input
        print("\nPlease enter mathematical problem or text (enter END to finish):")
        lines = []
        while True:
            line = input()
            if line.strip().upper() == "END":
                break
            lines.append(line)
        
        raw_input = "\n".join(lines)
        
        if not raw_input.strip():
            self._print_error("Input is empty")
            return
        
        # Initialize
        self._print_status("Initializing...")
        await self.agent.initialize_from_input(raw_input)
        
        # Display Memory
        self._print_header("Initial Memory")
        print(self.agent.get_memory_display())
        
        # Ask whether to start exploration
        start = input("\nStart automatic exploration? (y/n): ").strip().lower()
        if start != 'y':
            # Enter manual mode
            await self._manual_mode()
        else:
            # Automatic exploration
            max_rounds = input("Maximum rounds (default 50): ").strip()
            max_rounds = int(max_rounds) if max_rounds.isdigit() else 50
            
            checkpoint = input("Ask every how many rounds? (default 10, enter 0 to disable): ").strip()
            checkpoint = int(checkpoint) if checkpoint.isdigit() else 10
            
            self._print_status(f"Starting automatic exploration (max {max_rounds} rounds, ask every {checkpoint} rounds)")
            result = await self.agent.run(max_rounds=max_rounds, rounds_per_checkpoint=checkpoint)
            
            self._print_header("Exploration Results")
            print(f"Total rounds: {result['rounds']}")
            print("\nFinal Memory summary:")
            print(result['final_memory'])
    
    async def _manual_mode(self):
        """Manual mode"""
        self._print_header("Manual Mode")
        print("Commands:")
        print("  show      - Show current Memory")
        print("  add       - Add action")
        print("  text      - Add mathematical text")
        print("  run N [C] - Run N rounds, check every C rounds (default C=5)")
        print("  save      - Save Memory")
        print("  quit      - Exit")
        
        while True:
            cmd = input("\n> ").strip().lower()
            
            if cmd == "show":
                print(self.agent.get_memory_display())
            
            elif cmd == "add":
                self._manual_add_action()
            
            elif cmd == "text":
                print("Enter mathematical text (enter END to finish):")
                lines = []
                while True:
                    line = input()
                    if line.strip().upper() == "END":
                        break
                    lines.append(line)
                text = "\n".join(lines)
                if text:
                    self.agent.add_manual_text(text)
            
            elif cmd.startswith("run"):
                parts = cmd.split()
                n = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 10
                checkpoint = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 5
                await self.agent.run(max_rounds=n, rounds_per_checkpoint=checkpoint)
            
            elif cmd == "save":
                self.agent._save_memory("manual")
            
            elif cmd == "quit":
                break
            
            else:
                print("Unknown command")
    
    async def run_batch(self, input_file: str, output_dir: str, checkpoint: int = 0):
        """Batch mode"""
        self._print_header("Math Explorer Agent - Batch Mode")
        
        # Read input
        with open(input_file, 'r', encoding='utf-8') as f:
            raw_input = f.read()
        
        # Create Agent
        self.agent = MathExplorerAgent(save_path=output_dir)
        self._setup_event_handlers()
        
        # Run (batch mode disables checkpoint by default unless explicitly specified)
        await self.agent.initialize_from_input(raw_input)
        result = await self.agent.run(max_rounds=100, rounds_per_checkpoint=checkpoint)
        
        # Save final result
        self.agent._save_memory("final")
        
        self._print_header("Batch Processing Complete")
        print(result['final_memory'])


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Math Explorer Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python main.py
  
  # Batch mode
  python main.py --input problem.txt --output ./results
  
  # Continue from saved Memory
  python main.py --load ./memory/memory_20241227.json
        """
    )
    
    parser.add_argument(
        "--input", "-i",
        help="Input file path (batch mode)"
    )
    
    parser.add_argument(
        "--output", "-o",
        default=MEMORY_SAVE_PATH,
        help="Output directory path"
    )
    
    parser.add_argument(
        "--load", "-l",
        help="Load saved Memory file"
    )
    
    parser.add_argument(
        "--max-rounds", "-n",
        type=int,
        default=50,
        help="Maximum rounds"
    )
    
    parser.add_argument(
        "--checkpoint", "-c",
        type=int,
        default=10,
        help="Ask user every how many rounds (default 10, set to 0 to disable)"
    )
    
    args = parser.parse_args()
    
    cli = AgentCLI()
    
    if args.input:
        # Batch mode
        asyncio.run(cli.run_batch(args.input, args.output, args.checkpoint))
    else:
        # Interactive mode
        asyncio.run(cli.run_interactive())


if __name__ == "__main__":
    main()
