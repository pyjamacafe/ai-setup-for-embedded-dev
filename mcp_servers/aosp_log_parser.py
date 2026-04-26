import zipfile
import re
import os
from typing import Optional, Iterable
from collections import deque
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("AOSP_Debug_Server")
SEVERITY_MAP = {"V": 0, "D": 1, "I": 2, "W": 3, "E": 4, "F": 5}

def get_default_bugreport() -> Optional[str]:
    """Scans the current working directory for the first AOSP bugreport file."""
    # Look for standard bugreport zips first
    for file in os.listdir('.'):
        if file.startswith('bugreport-') and file.endswith('.zip'):
            return os.path.abspath(file)
    
    # Fallback to raw text files if a zip isn't found
    for file in os.listdir('.'):
        if file.startswith('bugreport-') and file.endswith('.txt'):
            return os.path.abspath(file)
            
    return None

def iter_lines_from_bugreport(bugreport_path: str) -> Iterable[str]:
    """Yields lines from either a zip file or a raw text bugreport."""
    if zipfile.is_zipfile(bugreport_path):
        with zipfile.ZipFile(bugreport_path, 'r') as zf:
            main_file = next((f for f in zf.namelist() if f.startswith("bugreport-") and f.endswith(".txt")), None)
            if not main_file:
                raise ValueError("Could not find main bugreport.txt inside the zip.")
            
            with zf.open(main_file) as f:
                for line in f:
                    try:
                        yield line.decode('utf-8').rstrip()
                    except UnicodeDecodeError:
                        continue
    else:
        with open(bugreport_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                yield line.rstrip()

@mcp.tool()
def query_logcat(
    bugreport_path: Optional[str] = None,
    tag: Optional[str] = None,
    level: str = "I",
    grep_pattern: Optional[str] = None,
    lines_before: int = 0,
    lines_after: int = 0
) -> str:
    """
    Extracts and filters logcat output from an Android bugreport (zip or txt).
    
    Args:
        bugreport_path: OPTIONAL. The absolute path to the bugreport file. CRITICAL INSTRUCTION: Leave this completely EMPTY (None) to automatically use the bugreport in the current directory.
        tag: The specific Android component tag to filter by (e.g., 'SurfaceFlinger', 'init'). 
        level: Minimum log severity level (V, D, I, W, E, F). Defaults to 'I'.
        grep_pattern: OPTIONAL. Text or regex to search WITHIN the message payload. Leave EMPTY if only filtering by tag. NEVER set this to the same value as the 'tag'.
        lines_before: Number of lines of context before a grep match.
        lines_after: Number of lines of context after a grep match.
    """
    if not bugreport_path:
        bugreport_path = get_default_bugreport()
        if not bugreport_path:
            return "Error: No bugreport_path provided, and no 'bugreport-*.zip' or '.txt' found in the server's current working directory."

    if not os.path.exists(bugreport_path):
        return f"Error: Could not locate bugreport at {bugreport_path}"

    min_severity = SEVERITY_MAP.get(level.upper(), 2)
    logcat_regex = re.compile(r'^\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\.\d{3}\s+(?:\S+\s+)?\d+\s+\d+\s+([VDIWEF])\s+(.*?):\s(.*)$')
    grep_regex = re.compile(grep_pattern, re.IGNORECASE) if grep_pattern else None

    results = []
    buffer = deque(maxlen=lines_before) if lines_before > 0 else None
    after_count = 0

    try:
        for decoded_line in iter_lines_from_bugreport(bugreport_path):
            match = logcat_regex.match(decoded_line)
            if match:
                line_sev_str, line_tag, line_msg = match.groups()
                line_tag = line_tag.strip()
                line_sev = SEVERITY_MAP.get(line_sev_str, 0)

                if line_sev < min_severity: continue
                if tag and tag != line_tag: continue

                if grep_regex:
                    if grep_regex.search(decoded_line):
                        if buffer and len(buffer) > 0:
                            results.extend(list(buffer))
                            buffer.clear()
                        results.append(decoded_line)
                        after_count = lines_after
                    else:
                        if after_count > 0:
                            results.append(decoded_line)
                            after_count -= 1
                        elif buffer is not None:
                            buffer.append(decoded_line)
                else:
                    results.append(decoded_line)

    except Exception as e:
        return f"Error parsing bugreport: {str(e)}"

    if not results:
        return "No logcat entries found matching the specified criteria."

    return "\n".join(results)


@mcp.tool()
def get_process_memory(
    bugreport_path: Optional[str] = None,
    process_name: Optional[str] = None
) -> str:
    """
    Extracts memory usage statistics (dumpsys meminfo) from the bugreport.
    
    Args:
        bugreport_path: OPTIONAL. The absolute path to the bugreport file. CRITICAL INSTRUCTION: Leave this completely EMPTY (None) to automatically use the bugreport in the current directory.
        process_name: OPTIONAL. The specific process to inspect (e.g., 'surfaceflinger', 'system_server'). Leave EMPTY to get the global memory summary.
    """
    if not bugreport_path:
        bugreport_path = get_default_bugreport()
        if not bugreport_path:
            return "Error: No bugreport_path provided, and no 'bugreport-*.zip' or '.txt' found in the server's current working directory."

    if not os.path.exists(bugreport_path):
        return f"Error: Could not locate bugreport at {bugreport_path}"

    results = []
    in_meminfo = False
    in_target_process = False
    
    try:
        for line in iter_lines_from_bugreport(bugreport_path):
            # BROADENED SEARCH: Check for both legacy and modern AOSP dumpstate headers
            if (line.startswith("DUMP OF SERVICE") and "meminfo" in line.lower()) or "------ DUMPSYS MEMINFO" in line:
                in_meminfo = True
                continue
            
            if in_meminfo:
                # Stop parsing if we hit the duration footer OR the next service block
                if "was the duration of dumpsys meminfo" in line:
                    break
                if line.startswith("DUMP OF SERVICE") and "meminfo" not in line.lower():
                    break
                
            if not in_meminfo:
                continue

            if process_name:
                # Looking for a specific process block (e.g., "** MEMINFO in pid 618 [surfaceflinger] **")
                if line.startswith("** MEMINFO in pid") and process_name.lower() in line.lower():
                    in_target_process = True
                    results.append(line)
                    continue
                elif in_target_process and line.startswith("** MEMINFO in pid"):
                    # Hit the next process block, we are done
                    break
                
                if in_target_process:
                    results.append(line)
            else:
                # Global Summary: Usually found towards the end of the meminfo dump
                if "Total PSS by" in line or "Total RAM:" in line:
                    in_target_process = True 
                
                if in_target_process:
                    results.append(line)

    except Exception as e:
        return f"Error parsing bugreport: {str(e)}"

    if not results:
        return f"Could not find memory info for '{process_name if process_name else 'global summary'}'."

    return "\n".join(results)

if __name__ == "__main__":
    mcp.run(transport='stdio')
