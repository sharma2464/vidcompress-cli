# Prompt & Diff Capture System

This folder contains a systematic record of all user prompts and their corresponding code changes in the VidCompress CLI project.

## Purpose

- **Traceability**: Every change can be traced back to the original user request
- **Learning**: Review past prompts to understand patterns and decision-making
- **Debugging**: Understand why certain changes were made
- **Collaboration**: Multiple agents can see what others have done
- **Documentation**: Built-in project history and evolution

## Folder Structure

```
prompts/
├── README.md                 # This file
├── config.json              # Configuration for the capture system
├── main/                    # Prompts related to main.py
├── convert/                 # Prompts related to convert.py
├── project/                 # Project-level prompts (README, AGENTS.md, etc.)
└── archive/                 # Older prompts, organized by month
```

## File Format

Each prompt is stored as a JSON file with the following structure:
- **timestamp**: When the prompt was made
- **session_id**: Unique identifier for the conversation
- **user_prompt**: Original user request text
- **files_modified**: List of files that were changed
- **diffs**: Detailed diff information for each file
- **agent_response**: Summary of what was done
- **context**: Platform, working directory, git branch, etc.

## Naming Convention

Files are named using the pattern: `YYYY-MM-DD_descriptive-name.json`

## Usage Guidelines for Agents

1. **Before making changes**: Create a new prompt file in the appropriate folder
2. **Document the request**: Copy the exact user prompt
3. **Track changes**: Note which files you plan to modify
4. **Capture diffs**: After making changes, run the capture script to record diffs
5. **Complete the record**: Update the file with results and context

## Automation

Use the `capture_prompt.py` script to automate the capture process:
```bash
python capture_prompt.py create "brief description"
# Make your changes
python capture_prompt.py complete
```

## Viewing History

To see the history of changes:
```bash
# List all prompts by date
ls -la prompts/*/*.json | sort

# Search for specific keywords
grep -r "keyword" prompts/

# View recent changes
find prompts/ -name "*.json" -mtime -7
```

## Integration with Git

All prompt files are tracked in Git and should be committed along with the changes they document:
```bash
git add prompts/
git commit -m "docs: capture prompt for feature X"
```

## Configuration

Edit `config.json` to customize:
- Default author information
- Preferred diff format
- File organization rules
- Validation settings