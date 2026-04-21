import os
import re
import subprocess
import platform
import sys
import math
import random
import json

# -------------------------
# Runtime / Environment
# -------------------------
apps = {}
modules = {}
variables = {
    "os_name": "macOS" if platform.system() == "Darwin" else platform.system()
}
functions = {}

# -------------------------
# Math Module
# -------------------------
mp_math = {
    # Trig
    "sin":       math.sin,
    "cos":       math.cos,
    "tan":       math.tan,
    "asin":      math.asin,
    "acos":      math.acos,
    "atan":      math.atan,
    "atan2":     math.atan2,
    # Rounding
    "round":     round,
    "floor":     math.floor,
    "ceil":      math.ceil,
    # Clamp
    "clamp":     lambda x, mn, mx: max(mn, min(mx, x)),
    # Random
    "rand":      random.random,
    "randint":   random.randint,
    "randfloat": random.uniform,
    # Misc
    "sqrt":      math.sqrt,
    "pow":       math.pow,
    "abs":       abs,
    "log":       math.log,
    "log10":     math.log10,
    # Constants
    "PI":        math.pi,
    "E":         math.e,
    "TAU":       math.tau,
}
modules["math"] = mp_math

# -------------------------
# MPKG
# -------------------------
MPKG_FILE = "mpkg.json"

def mpkg_install(package_name):
    print(f"Installing '{package_name}'...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", package_name],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"✓ '{package_name}' installed successfully.")
        try:
            imported = __import__(package_name)
            modules[package_name] = imported
            print(f"✓ '{package_name}' loaded into MP.")
        except ImportError:
            print(f"⚠ Installed but couldn't auto-import '{package_name}' (name mismatch).")
        # Save to mpkg.json
        data = {}
        if os.path.exists(MPKG_FILE):
            with open(MPKG_FILE) as f:
                data = json.load(f)
        data.setdefault("dependencies", {})[package_name] = "latest"
        with open(MPKG_FILE, "w") as f:
            json.dump(data, f, indent=2)
    else:
        print(f"✗ Install failed:\n{result.stderr.strip()}")

# -------------------------
# Helper Functions
# -------------------------
def exists(name):
    return name in apps

def replace_vars(text):
    tokens = re.split(r'(\W+)', text)
    return "".join(
        str(variables[token]) if token in variables else token
        for token in tokens
    )

def evaluate(expr):
    expr = replace_vars(expr)
    namespace = {k: v for k, v in variables.items()}
    namespace.update({k: v for k, v in modules.items()})
    # Flatten math module so sin(), cos() etc. are callable directly
    if "math" in modules:
        namespace.update(modules["math"])
    try:
        return eval(expr, {"__builtins__": {}}, namespace)
    except Exception as e:
        print(f"eval error: {e}")
        return None

def get_sys_fetch():
    raw_os = platform.system()
    is_android = "ANDROID_ROOT" in os.environ
    display_os = "macOS" if raw_os == "Darwin" else ("Android" if is_android else raw_os)

    if raw_os == "Darwin":
        logo = r"""
             #
             ###
            ####
          ####
          ##
####   ####
##########
##########
#######
######
##########
  ########"""
        stats = (
            f"\n\033[1mOS:\033[0m      macOS\n"
            f"\033[1mCORES:\033[0m   {os.cpu_count()} Threads\n"
            f"\033[1mARCH:\033[0m    {platform.machine()}\n"
            f"\033[1mHOST:\033[0m    {platform.node()}"
        )
    elif is_android:
        logo = (
            "##.                    ##\n"
            "         ##.                   ##\n"
            "        ###########\n"
            "    ##############\n"
            "####0######0#####"
        )
        stats = (
            f"\n\033[1mOS:\033[0m      Android\n"
            f"\033[1mCORES:\033[0m   Based\n"
            f"\033[1mTHREADS:\033[0m Based\n"
            f"\033[1mPLATFORM:\033[0m aarch64"
        )
    else:
        logo = r"""
             #####
            ##0#0##
           #YYYYY#"""
        stats = (
            f"\n\033[1mOS:\033[0m      {display_os}\n"
            f"\033[1mCORES:\033[0m   {os.cpu_count()} Threads\n"
            f"\033[1mARCH:\033[0m    {platform.machine()}\n"
            f"\033[1mHOST:\033[0m    {platform.node()}"
        )

    return logo + "\n" + stats

def osSystem_open(app_name):
    if not exists(app_name):
        print(f"Error: {app_name.capitalize()} not defined via #define.")
        return
    system = platform.system().lower()
    try:
        if system == "windows":
            cmd = "calc.exe" if app_name.lower() == "calculator" else app_name
            subprocess.Popen(cmd, shell=True)
        elif system == "linux":
            cmd = "gnome-calculator" if app_name.lower() == "calculator" else app_name
            subprocess.Popen([cmd])
        elif system == "darwin":
            cmd = "Calculator" if app_name.lower() == "calculator" else app_name
            subprocess.Popen(["open", "-a", cmd])
    except Exception as e:
        print(f"Launch failed: {e}")

# -------------------------
# Block Helpers
# -------------------------
def find_block_end(lines, start):
    """Find the closing } for a block, starting depth=1 from `start`."""
    depth = 1
    j = start
    while j < len(lines) and depth > 0:
        s = lines[j].strip()
        if re.match(r'^(if|while)\s+.+\{$', s):
            depth += 1
        elif s == "}":
            depth -= 1
        j += 1
    return j - 1  # index of the closing }

def find_else(lines, after):
    """Find 'else {' skipping blank lines and comments after a closing }."""
    j = after
    while j < len(lines):
        s = lines[j].strip()
        if s == "else {":
            return j
        if s and not s.startswith("//"):
            break  # hit real code, no else
        j += 1
    return None

# -------------------------
# Interpreter Logic
# -------------------------
def run_mp(file_path):
    if not os.path.isfile(file_path):
        print(f"Critical Error: File '{file_path}' not found.")
        return
    with open(file_path, "r") as f:
        lines = f.readlines()
    execute_lines(lines, 0)

def execute_lines(lines, start, end=None):
    if end is None:
        end = len(lines)

    i = start
    while i < end:
        line = lines[i].rstrip("\n")
        stripped = line.strip()

        if not stripped or stripped.startswith("//"):
            i += 1
            continue

        # --- #define app ---
        if stripped.startswith("#define "):
            name = stripped[8:].strip()
            apps[name] = True
            i += 1
            continue

        # --- #import module ---
        if stripped.startswith("#import "):
            mod = stripped[8:].strip()
            try:
                imported = __import__(mod)
                modules[mod] = imported
                print(f"Imported '{mod}' successfully.")
            except ImportError:
                print(f"Error: Module '{mod}' not found.")
            i += 1
            continue

        # --- mpkg install ---
        if stripped.startswith("mpkg install "):
            pkg = stripped[13:].strip()
            mpkg_install(pkg)
            i += 1
            continue

        # --- pyblock / endpy ---
        if stripped == "pyblock":
            py_lines = []
            j = i + 1
            while j < len(lines):
                s = lines[j].strip()
                if s == "endpy":
                    break
                py_lines.append(lines[j])
                j += 1
            py_code = "".join(py_lines)
            py_globals = {**globals(), **modules}
            try:
                exec(py_code, py_globals, variables)
            except Exception as e:
                print(f"pyblock error: {e}")
            # Sync any new variables back
            for k, v in list(variables.items()):
                variables[k] = v
            i = j + 1
            continue

        # --- def funcname ---
        if stripped.startswith("def "):
            func_name = stripped[4:].strip()
            body = []
            j = i + 1
            while j < len(lines):
                s = lines[j].strip()
                if s == "end":
                    break
                body.append(lines[j])
                j += 1
            functions[func_name] = body
            i = j + 1
            continue

        # --- function call ---
        if stripped in functions:
            execute_lines(functions[stripped], 0)
            i += 1
            continue

        # --- fetch ---
        if stripped == "fetch":
            print(get_sys_fetch())
            i += 1
            continue

        # --- open app ---
        if stripped.startswith("open "):
            app_name = stripped[5:].strip()
            osSystem_open(app_name)
            i += 1
            continue

        # --- print / say ---
        if stripped.startswith("print ") or stripped.startswith("say "):
            prefix_len = 6 if stripped.startswith("print ") else 4
            content = stripped[prefix_len:].strip()
            if (content.startswith('"') and content.endswith('"')) or \
               (content.startswith("'") and content.endswith("'")):
                print(replace_vars(content[1:-1]))
            else:
                result = evaluate(content)
                if result is None:
                    print(replace_vars(content))
                else:
                    print(result)
            i += 1
            continue

        # --- var = value ---
        assign_match = re.match(r'^([a-zA-Z_]\w*)\s*=\s*(.+)$', stripped)
        if assign_match:
            var_name = assign_match.group(1)
            raw_val = assign_match.group(2).strip()
            if (raw_val.startswith('"') and raw_val.endswith('"')) or \
               (raw_val.startswith("'") and raw_val.endswith("'")):
                variables[var_name] = raw_val[1:-1]
            else:
                result = evaluate(raw_val)
                variables[var_name] = result if result is not None else replace_vars(raw_val)
            i += 1
            continue

        # --- if condition { ---
        if_match = re.match(r'^if\s+(.+?)\s*\{$', stripped)
        if if_match:
            condition = if_match.group(1)
            block_end = find_block_end(lines, i + 1)

            else_line = find_else(lines, block_end + 1)
            else_start = None
            else_end = None
            if else_line is not None:
                else_start = else_line + 1
                else_end = find_block_end(lines, else_start)

            result = evaluate(condition)
            if result:
                execute_lines(lines, i + 1, block_end)
            elif else_start is not None:
                execute_lines(lines, else_start, else_end)
            i = (else_end + 1) if else_end else (block_end + 1)
            continue

        # --- while condition { ---
        while_match = re.match(r'^while\s+(.+?)\s*\{$', stripped)
        if while_match:
            condition = while_match.group(1)
            block_end = find_block_end(lines, i + 1)

            loop_limit = 10000
            iterations = 0
            while evaluate(condition) and iterations < loop_limit:
                execute_lines(lines, i + 1, block_end)
                iterations += 1
            if iterations >= loop_limit:
                print("Error: Loop limit reached (infinite loop protection).")
            i = block_end + 1
            continue

        # --- input var ---
        if stripped.startswith("input "):
            var_name = stripped[6:].strip()
            try:
                value = input(f"{var_name}> ")
                variables[var_name] = value
            except EOFError:
                variables[var_name] = ""
            i += 1
            continue

        # --- exit ---
        if stripped == "exit":
            print("Goodbye.")
            sys.exit(0)

        print(f"Warning: Unknown command -> '{stripped}'")
        i += 1

# -------------------------
# REPL
# -------------------------
def repl():
    print("MiniPhone OS Shell - type 'exit' to quit, 'fetch' for sysinfo")
    print("─" * 50)
    while True:
        try:
            line = input("mp> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if not line:
            continue
        execute_lines([line], 0)

# -------------------------
# Entry Point
# -------------------------
if __name__ == "__main__":
    if len(sys.argv) == 2:
        run_mp(sys.argv[1])
    else:
        repl()
