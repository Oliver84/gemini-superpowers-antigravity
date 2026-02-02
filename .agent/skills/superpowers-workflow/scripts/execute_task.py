#!/usr/bin/env python3
"""Unified execution script for Superpowers tasks.

Supports multiple backends (Gemini, Claude) and execution modes (Sequential/Streaming, Background/Log).
"""

import argparse
import json
import subprocess
import sys
import time
import uuid
import os
from pathlib import Path
from typing import Any, Dict

# Add script directory to path to import config
script_dir = Path(__file__).parent.resolve()
sys.path.append(str(script_dir))

import config

def find_repo_root(start: Path) -> Path:
    """Traverse upwards to find the repository root (containing .agent/)."""
    curr = start.resolve()
    for _ in range(10):
        if (curr / ".agent").exists():
            return curr
        if curr.parent == curr:
            break
        curr = curr.parent
    return Path.cwd()


def load_skill_instructions(skill_path: Path) -> str:
    """Load skill instructions from SKILL.md file."""
    if not skill_path.exists():
        return ""
    return skill_path.read_text(encoding="utf-8")


def run_gemini_backend(
    skill: str,
    task: str,
    repo_root: Path,
    yolo: bool,
    log_file: Path,
    stream_output: bool
) -> Dict[str, Any]:
    """Execute task using Gemini CLI."""

    # Load skill instructions
    skill_file = repo_root / f".agent/skills/superpowers-{skill}/SKILL.md"
    skill_instructions = load_skill_instructions(skill_file)

    if not skill_instructions:
        return {"success": False, "error": f"Skill not found: {skill_file}"}

    prompt = f"""You are a specialized subagent focused on: {skill}

IMPORTANT: You have ISOLATED CONTEXT. Do not assume knowledge from other conversations.

Task:
{task}

Skill Instructions:
{skill_instructions}

Requirements:
1. Follow the skill instructions exactly
2. Complete the task fully
3. Output ONLY the final result at the end
4. Do not include meta-commentary or thinking process in final output
5. Write any artifacts to artifacts/superpowers/subagent-{uuid.uuid4().hex[:8]}/

When complete, output:
---SUBAGENT-RESULT-START---
[Your final result here]
---SUBAGENT-RESULT-END---
"""

    cmd = ["gemini"]
    if yolo:
        cmd.append("--yolo")

    with open(log_file, "w", encoding="utf-8") as log:
        log.write(f"=== GEMINI EXECUTION START ===\n")
        log.write(f"Task: {task}\n\n")
        log.flush()

        # If streaming is requested (Sequential mode), we need to pipe stdout to both file and console
        # For simplicity in this implementation, we'll capture output and print it if needed,
        # or just run it and let the user see the file.

        # Actually, for sequential mode, we want to see it live.
        # But 'gemini' CLI is interactive.

        if stream_output:
             # Run interactively-ish (pipe to stdout)
             # But we also need to capture it for the log.
             process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=repo_root,
                text=True,
                shell=True # For Windows compatibility
             )

             process.stdin.write(prompt)
             process.stdin.close()

             full_output = []
             while True:
                 line = process.stdout.readline()
                 if not line and process.poll() is not None:
                     break
                 if line:
                     print(line, end="") # Stream to console
                     log.write(line)     # Write to log
                     full_output.append(line)
                     log.flush()

             returncode = process.poll()
             output_str = "".join(full_output)

        else:
            # Background mode - just capture
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                cwd=repo_root,
                timeout=600,
                shell=True
            )
            log.write(result.stdout)
            log.write("\n=== STDERR ===\n")
            log.write(result.stderr)
            returncode = result.returncode
            output_str = result.stdout

    # Extract result
    final_output = output_str
    if "---SUBAGENT-RESULT-START---" in output_str:
        parts = output_str.split("---SUBAGENT-RESULT-START---", 1)
        if len(parts) > 1:
            result_part = parts[1].split("---SUBAGENT-RESULT-END---", 1)
            final_output = result_part[0].strip()

    return {
        "success": returncode == 0,
        "output": final_output,
        "error": "" if returncode == 0 else "Process failed",
        "full_log": output_str
    }


def run_claude_backend(
    skill: str,
    task: str,
    repo_root: Path,
    yolo: bool,
    log_file: Path,
    stream_output: bool
) -> Dict[str, Any]:
    """Execute task using Claude Code CLI."""

    skill_file = repo_root / f".agent/skills/superpowers-{skill}/SKILL.md"
    skill_instructions = load_skill_instructions(skill_file)

    if not skill_instructions:
        return {"success": False, "error": f"Skill not found: {skill_file}"}

    # Construct the full context to pass to Claude
    full_prompt = f"""Task: {task}

Skill Instructions:
{skill_instructions}

Requirements:
1. Follow the skill instructions exactly.
2. Complete the task fully.
3. If creating files, just create them.
"""

    # Claude CLI command
    # -p: print mode (non-interactive)
    # --dangerously-skip-permissions: allow file edits without confirmation (required for autonomous exec)
    cmd = [
        "claude",
        "-p", "Follow the instructions provided in the input.",
        "--dangerously-skip-permissions"
    ]

    # Setup environment to ensure non-interactive behavior if needed
    env = os.environ.copy()

    with open(log_file, "w", encoding="utf-8") as log:
        log.write(f"=== CLAUDE EXECUTION START ===\n")
        log.write(f"Task: {task}\n\n")
        log.flush()

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=repo_root,
            text=True,
            env=env,
            shell=True # For Windows
        )

        # Pass the prompt via stdin
        process.stdin.write(full_prompt)
        process.stdin.close()

        full_output = []
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                if stream_output:
                    print(line, end="")
                log.write(line)
                full_output.append(line)
                log.flush()

        returncode = process.poll()
        output_str = "".join(full_output)

    return {
        "success": returncode == 0,
        "output": output_str,
        "error": "" if returncode == 0 else "Process failed",
        "full_log": output_str
    }


def execute_task(
    skill: str,
    task: str,
    repo_root: Path,
    yolo: bool = True,
    background: bool = False,
    output_format: str = "text",
) -> Dict[str, Any]:
    """
    Execute a task using the configured backend.
    """
    # Load configuration
    cfg = config.load_config(repo_root / ".agent")
    backend = cfg.get("execution_backend", "gemini")

    # Setup logging
    subagent_id = uuid.uuid4().hex[:8]
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    log_dir = repo_root / "artifacts" / "superpowers" / "subagents"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{backend}-{skill}-{timestamp}-{subagent_id}.log"

    start_time = time.time()

    if output_format == "text" and not background:
        print(f"🤖 Executing task using {backend.upper()}...")
        print(f"📝 Logging to: {log_file}")

    try:
        if backend == "claude":
            result = run_claude_backend(skill, task, repo_root, yolo, log_file, stream_output=not background)
        else:
            result = run_gemini_backend(skill, task, repo_root, yolo, log_file, stream_output=not background)

        duration_s = time.time() - start_time

        return {
            "success": result["success"],
            "output": result["output"],
            "error": result.get("error", ""),
            "log_file": str(log_file),
            "duration_s": duration_s,
            "subagent_id": subagent_id,
            "backend": backend
        }

    except Exception as e:
        duration_s = time.time() - start_time
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "log_file": str(log_file),
            "duration_s": duration_s,
            "subagent_id": subagent_id,
            "backend": backend
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute a Superpowers task")
    parser.add_argument("--skill", required=True, help="Skill to use")
    parser.add_argument("--task", required=True, help="Task description")
    parser.add_argument("--no-yolo", action="store_true", help="Disable auto-approval")
    parser.add_argument("--background", action="store_true", help="Run silently (for parallel mode)")
    parser.add_argument("--output-format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    repo_root = find_repo_root(Path.cwd())

    result = execute_task(
        skill=args.skill,
        task=args.task,
        repo_root=repo_root,
        yolo=not args.no_yolo,
        background=args.background,
        output_format=args.output_format,
    )

    if args.output_format == "json":
        print(json.dumps(result, indent=2))
        return 0 if result["success"] else 1

    # Text output summary
    if args.background:
        # Minimal output for background processes (will be collected by spawner)
        pass
    else:
        print(f"\n{'✅' if result['success'] else '❌'} Task completed in {result['duration_s']:.1f}s")
        if not result['success']:
            print(f"Error: {result['error']}")

    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
