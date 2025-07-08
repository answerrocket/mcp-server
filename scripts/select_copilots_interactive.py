#!/usr/bin/env python3
"""
Interactive TUI for selecting copilots with dropdown-style search using curses.
"""

import sys
import json
import curses
from typing import List, Dict, Set
from dataclasses import dataclass, field


@dataclass
class DropdownState:
    query: str = ""
    filtered_indices: List[int] = field(default_factory=list)
    selected_indices: Set[int] = field(default_factory=set)
    current_index: int = 0
    view_offset: int = 0
    confirm_dialog: bool = False
    confirm_save: bool = True


class CursesCopilotSelector:
    def __init__(self, copilots: List[Dict]):
        self.copilots = copilots
        self.state = DropdownState(filtered_indices=list(range(len(copilots))))
        
        # Pre-compute searchable text
        self.searchable_texts = []
        for copilot in copilots:
            searchable = " ".join([
                copilot.get('name', '').lower(),
                copilot.get('description', '').lower(),
                " ".join(skill.get('name', '').lower() for skill in copilot.get('skills', []))
            ])
            self.searchable_texts.append(searchable)
    
    def filter_copilots(self):
        """Filter copilots based on search query."""
        if not self.state.query:
            self.state.filtered_indices = list(range(len(self.copilots)))
        else:
            search_terms = self.state.query.lower().split()
            self.state.filtered_indices = []
            
            for idx, searchable_text in enumerate(self.searchable_texts):
                if all(term in searchable_text for term in search_terms):
                    self.state.filtered_indices.append(idx)
        
        # Adjust current index
        if self.state.filtered_indices:
            if self.state.current_index >= len(self.state.filtered_indices):
                self.state.current_index = len(self.state.filtered_indices) - 1
        else:
            self.state.current_index = 0
        
        self.state.view_offset = 0
    
    def draw_main(self, stdscr):
        """Draw the main interface."""
        height, width = stdscr.getmaxyx()
        stdscr.clear()
        
        # Header
        stdscr.addstr(0, 0, "🔍 Select Copilots to Install", curses.A_BOLD)
        stdscr.addstr(1, 0, "─" * min(width - 1, 80))
        
        # Search box
        stdscr.addstr(3, 0, "Search: ")
        stdscr.addstr(3, 8, self.state.query)
        stdscr.addstr(3, 8 + len(self.state.query), "█")
        
        # Results area calculation
        header_lines = 6
        footer_lines = 4
        available_lines = height - header_lines - footer_lines
        
        # Results
        if self.state.filtered_indices:
            stdscr.addstr(5, 0, f"Found {len(self.state.filtered_indices)} copilots:")
            
            # Adjust view offset
            if self.state.current_index < self.state.view_offset:
                self.state.view_offset = self.state.current_index
            elif self.state.current_index >= self.state.view_offset + available_lines:
                self.state.view_offset = self.state.current_index - available_lines + 1
            
            # Display results
            for i in range(min(available_lines, len(self.state.filtered_indices))):
                idx = self.state.view_offset + i
                if idx >= len(self.state.filtered_indices):
                    break
                
                copilot_idx = self.state.filtered_indices[idx]
                copilot = self.copilots[copilot_idx]
                
                # Format
                name = copilot.get('name', 'Unknown')
                skill_count = len(copilot.get('skills', []))
                skill_text = f"{skill_count} skill{'s' if skill_count != 1 else ''}"
                
                # Selection indicators
                is_selected = copilot_idx in self.state.selected_indices
                is_current = idx == self.state.current_index
                
                prefix = "▶ " if is_current else "  "
                checkbox = "[✓]" if is_selected else "[ ]"
                
                line = f"{prefix}{checkbox} {name} • {skill_text}"
                if len(line) > width - 2:
                    line = line[:width-5] + "..."
                
                y = header_lines + i
                if is_current:
                    stdscr.addstr(y, 0, line, curses.A_REVERSE)
                else:
                    stdscr.addstr(y, 0, line)
            
            # Scroll indicator
            if self.state.view_offset + available_lines < len(self.state.filtered_indices):
                remaining = len(self.state.filtered_indices) - self.state.view_offset - available_lines
                stdscr.addstr(height - footer_lines - 1, 2, f"↓ {remaining} more results")
        else:
            stdscr.addstr(5, 0, "No copilots match your search.")
        
        # Footer
        footer_y = height - 3
        stdscr.addstr(footer_y, 0, "─" * min(width - 1, 80))
        selected_count = len(self.state.selected_indices)
        stdscr.addstr(footer_y + 1, 0, f"{selected_count} copilot{'s' if selected_count != 1 else ''} selected")
        stdscr.addstr(footer_y + 2, 0, "↑↓: navigate • Enter: toggle • Type: search • Esc: finish")
    
    def draw_confirm(self, stdscr):
        """Draw confirmation dialog."""
        height, width = stdscr.getmaxyx()
        stdscr.clear()
        
        # Center the dialog
        center_y = height // 2 - 3
        
        selected_count = len(self.state.selected_indices)
        if selected_count > 0:
            stdscr.addstr(center_y, 5, f"{selected_count} copilot{'s' if selected_count != 1 else ''} selected")
            stdscr.addstr(center_y + 1, 5, "Save selections?")
            
            save_option = "[Save & Exit]"
            discard_option = "[Discard & Exit]"
            
            if self.state.confirm_save:
                stdscr.addstr(center_y + 3, 5, "▶ " + save_option, curses.A_REVERSE)
                stdscr.addstr(center_y + 4, 5, "  " + discard_option)
            else:
                stdscr.addstr(center_y + 3, 5, "  " + save_option)
                stdscr.addstr(center_y + 4, 5, "▶ " + discard_option, curses.A_REVERSE)
            
            stdscr.addstr(center_y + 6, 5, "↑↓: choose • Enter: confirm • Esc: cancel")
        else:
            stdscr.addstr(center_y, 5, "No copilots selected")
            stdscr.addstr(center_y + 1, 5, "Exit without selecting?")
            stdscr.addstr(center_y + 3, 5, "Press Enter to exit or Esc to continue")
    

    
    def run_curses(self, stdscr) -> List[Dict]:
        """Main curses loop."""
        # Setup
        curses.curs_set(0)  # Hide cursor
        stdscr.keypad(True)  # Enable special keys
        stdscr.timeout(50)  # Non-blocking input with 50ms timeout
        
        while True:
            # Draw appropriate screen
            if self.state.confirm_dialog:
                self.draw_confirm(stdscr)
            else:
                self.draw_main(stdscr)
            
            stdscr.refresh()
            
            # Get input
            try:
                key = stdscr.getch()
            except:
                continue
            
            if key == -1:  # No input
                continue
            
            # Handle input based on state
            if self.state.confirm_dialog:
                # Confirmation dialog input
                if key == curses.KEY_UP or key == curses.KEY_DOWN:
                    self.state.confirm_save = not self.state.confirm_save
                elif key == ord('\n') or key == ord('\r'):  # Enter
                    if len(self.state.selected_indices) > 0:
                        if self.state.confirm_save:
                            return [self.copilots[i] for i in sorted(self.state.selected_indices)]
                        else:
                            return []
                    else:
                        return []
                elif key == 27:  # ESC
                    self.state.confirm_dialog = False
            else:
                # Main interface input
                if key == curses.KEY_UP:
                    if self.state.current_index > 0:
                        self.state.current_index -= 1
                elif key == curses.KEY_DOWN:
                    if self.state.current_index < len(self.state.filtered_indices) - 1:
                        self.state.current_index += 1
                elif key == ord('\n') or key == ord('\r'):  # Enter
                    if self.state.filtered_indices:
                        copilot_idx = self.state.filtered_indices[self.state.current_index]
                        if copilot_idx in self.state.selected_indices:
                            self.state.selected_indices.remove(copilot_idx)
                        else:
                            self.state.selected_indices.add(copilot_idx)
                elif key == 27:  # ESC
                    self.state.confirm_dialog = True
                    self.state.confirm_save = True
                elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:
                    if self.state.query:
                        self.state.query = self.state.query[:-1]
                        self.filter_copilots()
                elif 32 <= key <= 126:  # Printable characters
                    self.state.query += chr(key)
                    self.filter_copilots()
                elif key == 3:  # Ctrl+C
                    return []
    
    def run(self) -> List[Dict]:
        """Run the selector."""
        try:
            return curses.wrapper(self.run_curses)
        except Exception as e:
            print(f"\nError: {e}", file=sys.stderr)
            return self.fallback_selection()
    
    def fallback_selection(self) -> List[Dict]:
        """Simple fallback selection."""
        print("\n=== Fallback Selection Mode ===", file=sys.stderr)
        for idx, copilot in enumerate(self.copilots[:10]):
            name = copilot.get('name', 'Unknown')
            skills = len(copilot.get('skills', []))
            print(f"{idx + 1}. {name} ({skills} skills)", file=sys.stderr)
        
        print("\nEnter numbers (comma-separated):", file=sys.stderr)
        try:
            selection = input().strip()
            if not selection:
                return []
            indices = [int(x.strip()) - 1 for x in selection.split(',')]
            return [self.copilots[i] for i in indices if 0 <= i < len(self.copilots)]
        except:
            return []


def main():
    """Main entry point."""
    # Check if we're in FIFO mode (first argument is FIFO path, second is JSON file)
    if len(sys.argv) == 3 and sys.argv[1].startswith('/tmp/'):
        fifo_path = sys.argv[1]
        json_file = sys.argv[2]
        
        print(f"Starting interactive copilot selector with FIFO: {fifo_path}", file=sys.stderr)
        
        try:
            with open(json_file, 'r') as f:
                copilot_data = json.load(f)
        except Exception as e:
            print(f"Error reading JSON file {json_file}: {e}", file=sys.stderr)
            sys.exit(1)
            
        selector = CursesCopilotSelector(copilot_data)
        selected = selector.run()
        
        # Write output to FIFO
        if selected:
            with open(fifo_path, 'w') as f:
                f.write(json.dumps(selected))
                f.flush()
        else:
            sys.exit(1)
            
        return
    
    # Original mode
    print("Starting interactive copilot selector...", file=sys.stderr)
    
    # Read copilot data
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
        print(f"Reading copilots from file: {json_file}", file=sys.stderr)
        try:
            with open(json_file, 'r') as f:
                content = f.read()
                if not content:
                    print(f"Error: JSON file {json_file} is empty", file=sys.stderr)
                    sys.exit(1)
                copilot_data = json.loads(content)
        except Exception as e:
            print(f"Error reading JSON file {json_file}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        copilot_data = json.load(sys.stdin)
    
    if not copilot_data:
        print("Error: No copilots found", file=sys.stderr)
        sys.exit(1)
    
    # Check if interactive mode is available
    if not sys.stdin.isatty():
        print(json.dumps(copilot_data))
        return
    
    # Run selector
    selector = CursesCopilotSelector(copilot_data)
    selected = selector.run()
    
    if not selected:
        print("No copilots selected", file=sys.stderr)
        sys.exit(1)
    
    # Output selected copilots as JSON
    print(json.dumps(selected))


if __name__ == "__main__":
    main()