# VidCompress CLI - Agent Guidelines

This file contains guidelines for agentic coding agents working on the VidCompress CLI project.

## Project Overview

VidCompress CLI is a cross-platform Python video compression tool that uses HandBrakeCLI or ffmpeg for video processing. It supports both remuxing (lossless container conversion) and encoding (compression with quality settings).

## Prompt Capture System (REQUIRED)

This project uses a systematic prompt and diff capture system to track all changes. **ALL AGENTS MUST USE THIS SYSTEM** for every modification.

### Quick Start Workflow
```bash
# 1. Create a new prompt session
python prompts/capture_prompt.py create "brief description" --prompt "Copy user's exact request"

# 2. Make your code changes
# (Edit files as needed)

# 3. Complete the session
python prompts/capture_prompt.py complete --response "Brief summary of what you did"
```

### Detailed Workflow
1. **Before making any changes**: Create a prompt session
   ```bash
   python prompts/capture_prompt.py create "add-feature-x" --component auto
   ```
   - Copy the user's exact prompt when prompted
   - The system will create backups of files you modify

2. **During development**: Work normally
   - Edit files as needed
   - The system tracks changes automatically

3. **After completing changes**: Complete the session
   ```bash
   python prompts/capture_prompt.py complete
   ```
   - Provide a brief summary of what was accomplished
   - The system captures diffs and updates the prompt record

4. **Commit your work**: Include the prompt file
   ```bash
   git add .
   git commit -m "feat: add feature X"
   ```

### Component Organization
- `main/`: Changes to main.py
- `convert/`: Changes to convert.py  
- `project/`: Documentation, AGENTS.md, README.md, etc.
- `archive/`: Older prompts organized by month

### Validation Requirements
- Every code change must have a corresponding prompt file
- Prompt files must include: user request, files modified, diffs, and summary
- Use the capture script - do not create prompt files manually

### Viewing History
```bash
# List recent prompts
python prompts/capture_prompt.py list

# Check current session status
python prompts/capture_prompt.py status

# View specific prompt file
cat prompts/main/2025-01-24_example.json
```

## Build/Test/Lint Commands

This project has zero external Python dependencies and uses only the Python standard library.

### Running the Application
```bash
# Main application
python main.py <input_path> <output_path> [options]

# Alternative converter
python convert.py <input_path> <output_dir>

# Examples
python main.py ./videos ./compressed
python main.py video.mov ./out --quality 22 --engine ffmpeg
python main.py ./videos ./out --remux
```

### Testing
No formal test suite exists. Manual testing involves:
```bash
# Test with sample video file
python main.py sample.mov ./test_output

# Test remux functionality
python main.py sample.mov ./test_output --remux

# Test with different engines
python main.py sample.mov ./test_output --engine handbrake
python main.py sample.mov ./test_output --engine ffmpeg
```

### Code Quality
- No linting tools configured
- No type checking tools configured
- Code follows standard Python conventions (see below)

## Code Style Guidelines

### Imports
- Standard library imports at the top
- Group by category: stdlib, third-party (none in this project), local
- Use `from pathlib import Path` for path operations
- Use `import subprocess` for external commands

### Formatting
- 4-space indentation
- Maximum line length: ~100 characters (evident from existing code)
- Use snake_case for variables and functions
- Use UPPER_CASE for constants

### Type Hints
- Use type hints for function parameters and return values
- `Path` type for file paths
- `str` for string parameters
- `int` for numeric parameters
- `bool` for boolean flags

Example:
```python
def process_one(
    input_path: Path,
    input_root: Path,
    output_root: Path,
    engine: str,
    quality: int,
    platform_name: str,
    single_file: bool,
    remux: bool,
) -> None:
```

### Naming Conventions
- Functions: snake_case (e.g., `detect_platform`, `select_engine`)
- Variables: snake_case (e.g., `platform_name`, `output_root`)
- Constants: UPPER_CASE (e.g., `VIDEO_EXTS`, `DEFAULT_QUALITY`)
- File names: snake_case (e.g., `main.py`, `convert.py`)

### Error Handling
- Use `sys.exit(1)` for fatal errors with clear error messages
- Check file existence before processing: `if not input_root.exists():`
- Validate subprocess return codes: `if res.returncode != 0:`
- Clean up failed outputs: `if output_path.exists(): output_path.unlink()`
- Use descriptive error messages with emoji indicators for consistency

### Logging/Output
- Use the `log()` function for consistent output formatting
- Include emoji indicators for different operations:
  - `🎞` for video processing
  - `✅` for success
  - `❌` for errors
  - `⏭` for skipped files
  - `🔁` for remux operations
- Always flush output: `print(msg, flush=True)`

### Platform Detection
- Use `detect_platform()` function for cross-platform compatibility
- Support platforms: macOS, Linux, Windows, Android (Termux)
- Platform-specific logic in engine selection and hardware acceleration

### External Dependencies
- Zero Python dependencies - use only standard library
- System dependencies: ffmpeg and/or HandBrakeCLI
- Check availability with `which()` function before use
- Graceful fallback when tools aren't available

### File Operations
- Use `pathlib.Path` for all file system operations
- Create directories with `mkdir(parents=True, exist_ok=True)`
- Use `rglob()` for recursive file searches
- Preserve directory structure in output

### Subprocess Management
- Use `subprocess.run()` with `check=False` for manual error handling
- Build commands as lists for proper argument handling
- Log commands before execution: `log("▶ " + " ".join(cmd))`

### Constants
- Define video extensions in `VIDEO_EXTS` set
- Use `DEFAULT_QUALITY = 28` for HandBrake RF-like quality
- Limit parallel workers: `MAX_WORKERS = 2` for GPU safety
- Output suffix: `OUTPUT_SUFFIX = "_compressed.mp4"`

### Function Organization
- Group related functions with comment headers:
  - `# ================= CONFIG =================`
  - `# ================= UTILS ==================`
  - `# ================= PLATFORM =================`
  - `# ================= ENGINES ==================`
  - `# ================= WORKER ==================`
  - `# ================= MAIN ====================`

### Argument Parsing
- Use `argparse.ArgumentParser()` for CLI interface
- Provide clear help messages and defaults
- Support choices for engine selection: `choices=["ffmpeg", "handbrake"]`
- Use `action="store_true"` for boolean flags

### Parallel Processing
- Use `ThreadPoolExecutor` for concurrent video processing
- Limit workers to prevent GPU overload
- Submit jobs with `pool.submit()` for fire-and-forget processing

## Architecture Notes

### Engine Selection
- Prioritize HandBrakeCLI on macOS for Apple VideoToolbox
- Fall back to ffmpeg on other platforms
- Respect user-specified engine when available
- Remuxing requires ffmpeg (not supported in HandBrakeCLI)

### Processing Pipeline
1. Detect platform and available engines
2. Collect video files from input path
3. For each file: check if already processed
4. Determine output path maintaining directory structure
5. Execute remux or encode based on user preference
6. Validate output and clean up failures

### Safety Features
- Prevent recursive compression (skip output directories)
- Skip already processed files (by suffix and location)
- Validate output files exist and have non-zero size
- Clean up failed outputs to prevent confusion

## Platform-Specific Behavior

### macOS
- Use HandBrakeCLI with Apple VideoToolbox when available
- Hardware acceleration via hevc_videotoolbox
- Optimize for streaming with `+faststart` flag

### Linux/Windows
- Use ffmpeg with libx265 software encoding
- CRF-based quality control
- Medium preset for balance of speed/quality

### Android (Termux)
- ffmpeg only (HandBrakeCLI not supported)
- CPU-based encoding
- Same quality settings as other platforms

## Agent Workflow Requirements

### MANDATORY: Prompt Capture for All Changes
**EVERY CODE CHANGE MUST BE DOCUMENTED USING THE PROMPT CAPTURE SYSTEM**

1. **Before starting any work**: Create a prompt session
   ```bash
   python prompts/capture_prompt.py create "descriptive-name" --component auto
   ```

2. **Copy the exact user request** when prompted

3. **Make your changes** normally

4. **Complete the session** before moving to other tasks:
   ```bash
   python prompts/capture_prompt.py complete
   ```

5. **Commit both code and prompt files**:
   ```bash
   git add .
   git commit -m "type: description"
   ```

### Validation Checklist
Before considering any work complete:
- [ ] Prompt session created with user's exact request
- [ ] All file changes captured in diffs
- [ ] Agent response summary provided
- [ ] Prompt file saved in correct component folder
- [ ] Both code and prompt files committed to git

### Session Management
- Use `python prompts/capture_prompt.py status` to check current session
- Use `python prompts/capture_prompt.py list` to view history
- Never manually edit prompt files - use the capture script

### Component Detection
The system automatically detects the correct folder based on files modified:
- `main/` → main.py changes
- `convert/` → convert.py changes  
- `project/` → documentation, config, AGENTS.md changes

## Future Development Guidelines

When adding new features:
1. **ALWAYS** start with prompt capture session
2. Maintain cross-platform compatibility
3. Add proper error handling and logging
4. Update README.md with new options
5. Test with both single files and directories
6. Preserve existing CLI interface
7. Consider hardware acceleration implications
8. Follow the established code organization pattern
9. **Complete prompt capture before moving to next task**