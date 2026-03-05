#!/usr/bin/env python3
"""
Prompt & Diff Capture System for VidCompress CLI

This script helps agents capture user prompts and code changes in a structured format.
It automates the creation and completion of prompt records with diffs and context.
"""

import sys
import json
import os
import subprocess
import argparse
from datetime import datetime, timezone
from pathlib import Path
import uuid
import re

# Fix Unicode output for Windows
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ================= CONFIG =================
PROMPTS_DIR = Path(__file__).parent
CONFIG_FILE = PROMPTS_DIR / "config.json"
SESSION_FILE = PROMPTS_DIR / ".current_session.json"

# ================= UTILS =================
def load_config():
    """Load configuration from config.json"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_config(config):
    """Save configuration to config.json"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

def get_session_id():
    """Generate or retrieve session ID"""
    config = load_config()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    random_suffix = str(uuid.uuid4())[:8]
    return f"session_{timestamp}_{random_suffix}"

def get_git_info():
    """Get git branch and status information"""
    try:
        # Get current branch
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=False
        )
        branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
        
        # Get git status (clean/dirty)
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, check=False
        )
        is_clean = len(status_result.stdout.strip()) == 0 if status_result.returncode == 0 else False
        
        return {
            "branch": branch,
            "is_clean": is_clean,
            "has_git": True
        }
    except Exception:
        return {
            "branch": "unknown",
            "is_clean": False,
            "has_git": False
        }

def get_platform_info():
    """Get platform and environment information"""
    import platform
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "python_version": platform.python_version(),
        "working_directory": str(Path.cwd()),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def determine_component_folder(files_modified):
    """Determine which folder to use based on files modified"""
    config = load_config()
    folders = config.get("folders", {})
    
    # Count matches for each folder
    folder_scores = {}
    for folder_name, folder_config in folders.items():
        score = 0
        folder_files = set(folder_config.get("files", []))
        for file in files_modified:
            if file in folder_files:
                score += 1
        folder_scores[folder_name] = score
    
    # Return folder with highest score, default to "project"
    if folder_scores:
        best_folder = max(folder_scores.keys(), key=lambda k: folder_scores[k])
        if folder_scores[best_folder] > 0:
            return best_folder
    
    return "project"

def generate_diff(file_path):
    """Generate unified diff for a file"""
    try:
        # Try to get git diff first
        result = subprocess.run(
            ["git", "diff", "--unified=3", str(file_path)],
            capture_output=True, text=True, check=False
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    
    # Fallback: create a simple diff by comparing with backup
    backup_path = Path(file_path).with_suffix(file_path.suffix + ".backup")
    if backup_path.exists():
        try:
            result = subprocess.run(
                ["diff", "-u3", str(backup_path), str(file_path)],
                capture_output=True, text=True, check=False
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
    
    return None

def create_backup(file_path):
    """Create backup of file before modification"""
    file_path = Path(file_path)
    if file_path.exists():
        backup_path = file_path.with_suffix(file_path.suffix + ".backup")
        try:
            import shutil
            shutil.copy2(file_path, backup_path)
            return True
        except Exception:
            pass
    return False

# ================= COMMANDS =================
def cmd_create(args):
    """Create a new prompt capture session"""
    description = args.description or "unnamed_change"
    component = args.component or "project"
    
    # Generate session info
    session_id = get_session_id()
    timestamp = datetime.now(timezone.utc).isoformat()
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Create filename
    safe_description = re.sub(r'[^a-zA-Z0-9_-]', '_', description.lower())
    filename = f"{date_str}_{safe_description}.json"
    
    # Determine folder
    if component == "auto":
        # Will be determined when files are specified
        component = "project"
    
    # Create prompt file path
    prompt_dir = PROMPTS_DIR / component
    prompt_dir.mkdir(parents=True, exist_ok=True)
    prompt_file = prompt_dir / filename
    
    # Get user prompt
    if args.prompt:
        user_prompt = args.prompt
    else:
        print("Enter the user prompt (press Enter on empty line to finish):")
        lines = []
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
        user_prompt = "\n".join(lines)
    
    # Create initial prompt record
    prompt_data = {
        "timestamp": timestamp,
        "session_id": session_id,
        "user_prompt": user_prompt,
        "files_modified": [],
        "diffs": {},
        "agent_response": "",
        "context": {
            "platform": get_platform_info(),
            "git": get_git_info(),
            "component": component,
            "description": description
        },
        "status": "created"
    }
    
    # Save prompt file
    with open(prompt_file, 'w', encoding='utf-8') as f:
        json.dump(prompt_data, f, indent=2)
    
    # Save current session info
    session_info = {
        "session_id": session_id,
        "prompt_file": str(prompt_file),
        "component": component,
        "created_files": []
    }
    with open(SESSION_FILE, 'w', encoding='utf-8') as f:
        json.dump(session_info, f, indent=2)
    
    print(f"✅ Created prompt session: {session_id}")
    print(f"📁 Prompt file: {prompt_file}")
    print(f"📝 Now make your changes, then run: python capture_prompt.py complete")
    
    # Create backups if files specified
    if args.files:
        for file_path in args.files:
            if create_backup(file_path):
                print(f"📦 Created backup: {file_path}.backup")

def cmd_add_file(args):
    """Add a file to the current session"""
    if not SESSION_FILE.exists():
        print("❌ No active session. Use 'create' command first.")
        return
    
    with open(SESSION_FILE, 'r') as f:
        session_info = json.load(f)
    
    prompt_file = Path(session_info["prompt_file"])
    file_path = args.file
    
    # Create backup before modification
    if create_backup(file_path):
        print(f"📦 Created backup: {file_path}.backup")
    
    # Update session info
    session_info["created_files"].append(file_path)
    with open(SESSION_FILE, 'w') as f:
        json.dump(session_info, f, indent=2)
    
    print(f"➕ Added file to session: {file_path}")

def cmd_complete(args):
    """Complete the current prompt session with diffs and results"""
    if not SESSION_FILE.exists():
        print("❌ No active session. Use 'create' command first.")
        return
    
    with open(SESSION_FILE, 'r') as f:
        session_info = json.load(f)
    
    prompt_file = Path(session_info["prompt_file"])
    
    if not prompt_file.exists():
        print(f"❌ Prompt file not found: {prompt_file}")
        return
    
    # Load current prompt data
    with open(prompt_file, 'r') as f:
        prompt_data = json.load(f)
    
    # Get files modified (auto-detect if not specified)
    files_modified = []
    if args.files:
        files_modified = args.files
    else:
        # Auto-detect modified files from git status
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, check=False
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split(maxsplit=1)
                        if len(parts) == 2:
                            file_path = parts[1]
                            if Path(file_path).exists():
                                files_modified.append(file_path)
        except Exception:
            pass
    
    # Generate diffs for each file
    diffs = {}
    for file_path in files_modified:
        diff_content = generate_diff(file_path)
        if diff_content:
            diffs[file_path] = {
                "type": "edit",
                "diff_content": diff_content
            }
    
    # Get agent response
    if args.response:
        agent_response = args.response
    else:
        print("Enter summary of what was done (press Enter on empty line to finish):")
        lines = []
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
        agent_response = "\n".join(lines)
    
    # Update prompt data
    prompt_data["files_modified"] = files_modified
    prompt_data["diffs"] = diffs
    prompt_data["agent_response"] = agent_response
    prompt_data["status"] = "completed"
    prompt_data["completed_timestamp"] = datetime.now(timezone.utc).isoformat()
    
    # Re-determine component if auto
    if prompt_data["context"]["component"] == "project" and files_modified:
        best_component = determine_component_folder(files_modified)
        if best_component != "project":
            # Move file to appropriate folder
            new_dir = PROMPTS_DIR / best_component
            new_dir.mkdir(parents=True, exist_ok=True)
            new_prompt_file = new_dir / prompt_file.name
            
            prompt_file.rename(new_prompt_file)
            prompt_file = new_prompt_file
            prompt_data["context"]["component"] = best_component
            print(f"📁 Moved prompt file to: {prompt_file}")
    
    # Save updated prompt data
    with open(prompt_file, 'w', encoding='utf-8') as f:
        json.dump(prompt_data, f, indent=2)
    
    # Clean up session file
    SESSION_FILE.unlink()
    
    # Clean up backup files
    for file_path in files_modified:
        backup_path = Path(str(file_path) + ".backup")
        if backup_path.exists():
            try:
                backup_path.unlink()
                print(f"🗑️ Cleaned backup: {backup_path}")
            except Exception:
                pass
    
    print(f"✅ Completed prompt session: {session_info['session_id']}")
    print(f"📁 Prompt file: {prompt_file}")
    print(f"📝 Files modified: {len(files_modified)}")
    print(f"🔍 Diffs captured: {len(diffs)}")

def cmd_status(args):
    """Show current session status"""
    if not SESSION_FILE.exists():
        print("ℹ️ No active session.")
        return
    
    with open(SESSION_FILE, 'r') as f:
        session_info = json.load(f)
    
    prompt_file = Path(session_info["prompt_file"])
    
    print(f"📋 Active Session: {session_info['session_id']}")
    print(f"📁 Prompt File: {prompt_file}")
    print(f"📂 Component: {session_info['component']}")
    
    if prompt_file.exists():
        with open(prompt_file, 'r') as f:
            prompt_data = json.load(f)
        print(f"📝 Status: {prompt_data.get('status', 'unknown')}")
        print(f"📅 Created: {prompt_data.get('timestamp', 'unknown')}")

def cmd_list(args):
    """List all prompt files"""
    component = args.component
    
    if component:
        prompt_dir = PROMPTS_DIR / component
        if not prompt_dir.exists():
            print(f"❌ Component folder not found: {component}")
            return
    else:
        prompt_dir = PROMPTS_DIR
    
    # Find all JSON files
    prompt_files = list(prompt_dir.rglob("*.json"))
    prompt_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    
    if not prompt_files:
        print("ℹ️ No prompt files found.")
        return
    
    print(f"📋 Found {len(prompt_files)} prompt file(s):")
    for prompt_file in prompt_files[:10]:  # Show last 10
        try:
            with open(prompt_file, 'r') as f:
                data = json.load(f)
            
            relative_path = prompt_file.relative_to(PROMPTS_DIR)
            status = data.get("status", "unknown")
            timestamp = data.get("timestamp", "unknown")[:16]
            files_count = len(data.get("files_modified", []))
            
            print(f"  📄 {relative_path}")
            print(f"     📅 {timestamp} | 📝 {status} | 📁 {files_count} files")
        except Exception as e:
            print(f"  ❌ {prompt_file.name} (error: {e})")

# ================= MAIN =================
def main():
    parser = argparse.ArgumentParser(
        description="Prompt & Diff Capture System for VidCompress CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python capture_prompt.py create "add new feature" --prompt "User request here"
  python capture_prompt.py add-file main.py
  python capture_prompt.py complete --response "Summary of changes"
  python capture_prompt.py status
  python capture_prompt.py list --component main
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create new prompt session')
    create_parser.add_argument('description', help='Brief description of the change')
    create_parser.add_argument('--prompt', help='User prompt text')
    create_parser.add_argument('--component', choices=['main', 'convert', 'project', 'auto'], 
                              default='auto', help='Component folder')
    create_parser.add_argument('--files', nargs='*', help='Files that will be modified')
    
    # Add-file command
    add_parser = subparsers.add_parser('add-file', help='Add file to current session')
    add_parser.add_argument('file', help='File path to add')
    
    # Complete command
    complete_parser = subparsers.add_parser('complete', help='Complete current session')
    complete_parser.add_argument('--response', help='Agent response summary')
    complete_parser.add_argument('--files', nargs='*', help='Files that were modified')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show current session status')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List prompt files')
    list_parser.add_argument('--component', choices=['main', 'convert', 'project'], 
                           help='Filter by component')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'create':
            cmd_create(args)
        elif args.command == 'add-file':
            cmd_add_file(args)
        elif args.command == 'complete':
            cmd_complete(args)
        elif args.command == 'status':
            cmd_status(args)
        elif args.command == 'list':
            cmd_list(args)
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()