import os
import re
import subprocess
import platform
import sys
import math
import random
import json
import atexit
import importlib.util
from pathlib import Path
from types import SimpleNamespace

__version__ = "1.5-max-optimized"

def _load_mp_stdlib_module():
    stdlib_path = os.path.join(os.path.dirname(__file__), "mp.stdlib.py")
    spec = importlib.util.spec_from_file_location("mp_stdlib", stdlib_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

mp_stdlib = _load_mp_stdlib_module()

def cleanup_pycache():
    repo_root = Path(__file__).resolve().parent
    for cache_dir in repo_root.rglob("__pycache__"):
        if cache_dir.is_dir():
            for item in cache_dir.iterdir():
                try: intel = item.unlink()
                except OSError: pass
            try: cache_dir.rmdir()
            except OSError: pass
    for pyc_file in repo_root.glob("*.pyc"):
        try: pyc_file.unlink()
        except OSError: pass

atexit.register(cleanup_pycache)

# -------------------------
# Runtime Memory Layout
# -------------------------
apps = {}
modules = {}
variables = {
    "os_name": "macOS" if platform.system() == "Darwin" else platform.system()
}
functions = {}

# -------------------------
# Built-in Math Module
# -------------------------
mp_math = {
    "sin":       math.sin, "cos":       math.cos, "tan":       math.tan,
    "asin":      math.asin, "acos":      math.acos, "atan":      math.atan,
    "atan2":     math.atan2, "round":     round, "floor":     math.floor,
    "ceil":      math.ceil, "clamp":     lambda x, mn, mx: max(mn, min(mx, x)),
    "rand":      random.random, "randint":   random.randint, "randfloat": random.uniform,
    "sqrt":      math.sqrt, "pow":       math.pow, "abs":       abs,
    "log":       math.log, "log10":     math.log10, "PI":        math.pi,
    "E":         math.e, "TAU":       math.tau,
}
modules["math"] = mp_math

# -------------------------
# PKG Management System
# -------------------------
MPKG_FILE = "mpkg.json"
PYKG_FILE = "pykg.json"

def _pip_install(package_name):
    try:
        from pip._internal.cli.main import main as pip_main
    except ImportError:
        try:
            from pip._internal import main as pip_main
        except ImportError:
            return None, "pip internal API unavailable"
    try: return pip_main(["install", package_name]), None
    except Exception as exc: return 1, str(exc)

def pykg_install(package_name):
    print(f"Installing Python package '{package_name}'...")
    returncode, error = _pip_install(package_name)
    stderr = ""
    if returncode is None:
        result = subprocess.run([sys.executable, "-m", "pip", "install", package_name], capture_output=True, text=True)
        returncode = result.returncode
        stderr = result.stderr.strip()
    elif error:
        returncode = 1
        stderr = error

    if returncode == 0:
        print(f"✓ '{package_name}' installed successfully.")
        try:
            modules[package_name] = __import__(package_name)
            print(f"✓ '{package_name}' auto-loaded into environment.")
        except ImportError: pass
        data = {}
        if os.path.exists(PYKG_FILE):
            with open(PYKG_FILE) as f: data = json.load(f)
        data.setdefault("dependencies", {})[package_name] = "latest"
        with open(PYKG_FILE, "w") as f: json.dump(data, f, indent=2)
    else:
        print(f"✗ Install failed:\n{stderr}")

def mpkg_install(package_name):
    print(f"Installing MP standard library package '{package_name}'...")
    alias = package_name if package_name.startswith("std/") else f"std/{package_name}"
    std_mod = mp_stdlib.load_std_module(alias)
    if std_mod is None:
        print(f"Error: MP stdlib package '{package_name}' not found.")
        return
    mod_name = package_name.split("/", 1)[1] if package_name.startswith("std/") else package_name
    modules[mod_name] = SimpleNamespace(**std_mod)
    print(f"✓ '{package_name}' loaded into MP context.")
    data = {}
    if os.path.exists(MPKG_FILE):
        with open(MPKG_FILE) as f: data = json.load(f)
    data.setdefault("dependencies", {})[package_name] = "builtin"
    with open(MPKG_FILE, "w") as f: json.dump(data, f, indent=2)

# -------------------------
# Dynamic Evaluation Core
# -------------------------
def replace_vars(text):
    tokens = re.split(r'(\W+)', text)
    return "".join(str(variables[token]) if token in variables else token for token in tokens)

def evaluate(expr):
    expr = replace_vars(expr)
    namespace = {**variables, **modules}
    if "math" in modules:
        namespace.update(modules["math"] if isinstance(modules["math"], dict) else modules["math"].__dict__)
    
    # Int, Float types whitelisted to allow mathematical loop evaluation without breaking counters
    safe_builtins = {"int": int, "float": float, "str": str, "bool": bool, "abs": abs, "round": round}
    try:
        return eval(expr, {"__builtins__": safe_builtins}, namespace)
    except Exception:
        return None

def get_sys_fetch():
    logo = "■ MiniPhone Engine OS ■"
    stats = f"OS: {variables.get('os_name')}\nCores: {os.cpu_count()} Threads\nArch: {platform.machine()}"
    return f"{logo}\n{stats}"

def osSystem_open(app_name):
    if app_name not in apps:
        print(f"Error: {app_name} not defined via #define.")
        return
    system = platform.system().lower()
    try:
        if system == "windows": subprocess.Popen(app_name, shell=True)
        elif system == "darwin": subprocess.Popen(["open", "-a", app_name])
        else: subprocess.Popen([app_name])
    except Exception as e: print(f"Launch failed: {e}")

# -------------------------
# Block Offsets
# -------------------------
def find_block_end(lines, start):
    depth = 1
    j = start
    while j < len(lines) and depth > 0:
        s = lines[j].strip()
        if re.match(r'^(if|while)\s+.+\{$', s): depth += 1
        elif s == "}": depth -= 1
        j += 1
    return j - 1

def find_else(lines, after):
    j = after
    while j < len(lines):
        s = lines[j].strip()
        if s == "else {": return j
        if s and not s.startswith("//"): break
        j += 1
    return None

# -------------------------
# Optimized Runtime Pipeline
# -------------------------
def run_mp(file_path):
    if not os.path.isfile(file_path): return
    with open(file_path, "r") as f:
        lines = f.readlines()
    execute_lines(lines, 0)

def execute_lines(lines, start, end=None):
    if end is None: end = len(lines)

    i = start
    while i < end:
        line = lines[i].rstrip("\n")
        stripped = line.strip()

        if not stripped or stripped.startswith("//"):
            i += 1
            continue

        if stripped.startswith("#define "):
            apps[stripped[8:].strip()] = True
            i += 1
            continue

        if stripped.startswith("#import "):
            mod = stripped[8:].strip()
            if mod.startswith("std/"):
                std_mod = mp_stdlib.load_std_module(mod)
                if std_mod is not None:
                    if "std" not in modules: modules["std"] = SimpleNamespace()
                    setattr(modules["std"], mod.split("/", 1)[1], SimpleNamespace(**std_mod))
            else:
                try: modules[mod] = __import__(mod)
                except ImportError: print(f"Error: Module {mod} not found.")
            i += 1
            continue

        if stripped.startswith("mpkg install "):
            mpkg_install(stripped[13:].strip())
            i += 1
            continue

        if stripped.startswith("pykg install "):
            pykg_install(stripped[13:].strip())
            i += 1
            continue

        if stripped == "pyblock":
            py_lines = []
            j = i + 1
            while j < len(lines):
                if lines[j].strip() == "endpy": break
                py_lines.append(lines[j])
                j += 1
            try: exec("".join(py_lines), {**globals(), **modules}, variables)
            except Exception as e: print(f"pyblock error: {e}")
            i = j + 1
            continue

        if stripped.startswith("def "):
            func_name = stripped[4:].strip()
            body = []
            j = i + 1
            while j < len(lines):
                if lines[j].strip() == "end": break
                body.append(lines[j])
                j += 1
            functions[func_name] = body
            i = j + 1
            continue

        if stripped in functions:
            execute_lines(functions[stripped], 0)
            i += 1
            continue

        if stripped == "fetch":
            print(get_sys_fetch())
            i += 1
            continue

        if stripped.startswith("open "):
            osSystem_open(stripped[5:].strip())
            i += 1
            continue

        if stripped.startswith("print ") or stripped.startswith("say "):
            prefix_len = 6 if stripped.startswith("print ") else 4
            content = stripped[prefix_len:].strip()
            if (content.startswith('"') and content.endswith('"')) or (content.startswith("'") and content.endswith("'")):
                print(replace_vars(content[1:-1]))
            else:
                res = evaluate(content)
                print(res if res is not None else replace_vars(content))
            i += 1
            continue

        if stripped.startswith("input "):
            var_name = stripped[6:].strip()
            try: variables[var_name] = input(f"{var_name}> ")
            except EOFError: variables[var_name] = ""
            i += 1
            continue

        if stripped == "exit":
            sys.exit(0)

        # Assignments Channel
        assign_match = re.match(r'^([a-zA-Z_]\w*)\s*=\s*(.+)$', stripped)
        if assign_match:
            vname, raw_val = assign_match.group(1), assign_match.group(2).strip()
            if (raw_val.startswith('"') and raw_val.endswith('"')) or (raw_val.startswith("'") and raw_val.endswith("'")):
                variables[vname] = raw_val[1:-1]
            else:
                res = evaluate(raw_val)
                variables[vname] = res if res is not None else replace_vars(raw_val)
            i += 1
            continue

        if_match = re.match(r'^if\s+(.+?)\s*\{$', stripped)
        if if_match:
            cond = if_match.group(1)
            block_end = find_block_end(lines, i + 1)
            else_line = find_else(lines, block_end + 1)
            
            estart = eend = None
            if else_line is not None:
                estart = else_line + 1
                eend = find_block_end(lines, estart)

            if evaluate(cond): execute_lines(lines, i + 1, block_end)
            elif estart is not None: execute_lines(lines, estart, eend)
            i = (eend + 1) if eend else (block_end + 1)
            continue

        # --- AST-TOKENIZED FAST WHILE LOOP CHANNEL ---
        while_match = re.match(r'^while\s+(.+?)\s*\{$', stripped)
        if while_match:
            condition = while_match.group(1)
            block_end = find_block_end(lines, i + 1)
            
            # Pre-compile the lines into a structured array of tokens ONCE
            loop_lines = lines[i + 1:block_end]
            tokenized_payload = [ln.strip() for ln in loop_lines if ln.strip() and not ln.strip().startswith("//")]

            loop_limit = 1000000000  # Built to scale past 1 Billion iteration runs
            iterations = 0
            
            while evaluate(condition) and iterations < loop_limit:
                execute_lines(tokenized_payload, 0)
                iterations += 1
                
            if iterations >= loop_limit:
                print("Error: Loop limit reached (infinite loop protection).")
            i = block_end + 1
            continue

        print(f"Warning: Unknown command -> '{stripped}'")
        i += 1

# -------------------------
# REPL Shell Interaction
# -------------------------
def repl():
    print("MiniPhone OS Shell - type 'exit' to quit, 'fetch' for sysinfo")
    print("─" * 50)
    while True:
        try: line = input("mp> ").strip()
        except (EOFError, KeyboardInterrupt): break
        if not line: continue
        execute_lines([line], 0)

if __name__ == "__main__":
    if len(sys.argv) == 2: run_mp(sys.argv[1])
    else: repl()
