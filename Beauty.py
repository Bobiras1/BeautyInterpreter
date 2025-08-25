#!/usr/bin/env python3
"""

Three small interpreters (Anna, Alex, Rosa).
- Each interpreter can run a multi-line source with Class(source).run()
- Each interpreter has a REPL that uses the same engine
- CLI supports: python trio_langs.py <anna|alex|rosa> [file] [--repl]

This is intentionally small and easy to extend.
"""
from __future__ import annotations
import argparse
import math
import random
import sys
from typing import Dict, Any

# --------------------------
# Safe-ish builtins available in expressions
# --------------------------
BASE_BUILTINS: Dict[str, Any] = {
    "len": len,
    "range": lambda n: list(range(int(n))),
    "abs": abs,
    "min": min,
    "max": max,
    "floor": math.floor,
    "ceil": math.ceil,
    "sqrt": math.sqrt,
    "exp": math.exp,
    "log": math.log,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "sigmoid": lambda x: 1 / (1 + math.exp(-x)),
    "mean": lambda xs: sum(xs) / (len(xs) or 1),
    "dot": lambda a, b: sum(x * y for x, y in zip(a, b)),
    "rand": random.random,
    "math": math,
}

def make_env(extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Create an execution environment mapping names to values.
    Safe globals (functions) live in SAFE_GLOBALS; per-program variables live in env."""
    env: Dict[str, Any] = {}
    if extra:
        env.update(extra)
    return env

SAFE_GLOBALS = dict(BASE_BUILTINS)  # used as globals for eval/exec

# --------------------------
# Common helpers
# --------------------------
def eval_expr(src: str, env: Dict[str, Any]) -> Any:
    """Evaluate an expression using SAFE_GLOBALS and env as locals."""
    try:
        return eval(src, SAFE_GLOBALS, env)
    except Exception as e:
        raise RuntimeError(f"Eval error: {e}")

def exec_stmt(src: str, env: Dict[str, Any]) -> None:
    """Execute a statement (or statement block)."""
    try:
        exec(src, SAFE_GLOBALS, env)
    except Exception as e:
        raise RuntimeError(f"Exec error: {e}")

# --------------------------
# Anna — simple declarative-style
#   - name := expr    assign
#   - print expr
#   - expression lines evaluate and are ignored (or can be used to compute)
# --------------------------
class Anna:
    def __init__(self, source: str, env: Dict[str, Any] | None = None):
        self.lines = source.splitlines()
        self.env = make_env(env)

    def run(self) -> Dict[str, Any]:
        for raw in self.lines:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            # assignment: name := expr
            if ":=" in line:
                name, expr = [p.strip() for p in line.split(":=", 1)]
                val = eval_expr(expr, self.env)
                self.env[name] = val
            elif line.startswith("print "):
                expr = line[len("print "):].strip()
                val = eval_expr(expr, self.env)
                print(val)
            else:
                # evaluate expression but don't print unless it returns something we care about
                try:
                    _ = eval_expr(line, self.env)
                except RuntimeError:
                    # If it's not a valid expression, treat as error
                    raise
        return self.env

    # REPL uses same engine
    @staticmethod
    def repl():
        print("Anna REPL — :help for commands. Use `name := expr` and `print expr`.")
        env = make_env()
        while True:
            try:
                line = input("anna> ").rstrip()
            except (KeyboardInterrupt, EOFError):
                print(); break
            if not line:
                continue
            if line.startswith(":"):
                cmd = line[1:].strip().split(maxsplit=1)
                c = cmd[0].lower()
                arg = cmd[1] if len(cmd) > 1 else ""
                if c in ("q", "quit", "exit"):
                    break
                if c in ("h", "help"):
                    print("Commands: :help, :examples, :env, :load <file>, :reset, :quit")
                    print("Anna syntax: name := expr  |  print expr")
                    continue
                if c == "examples":
                    print('Example:\n  message := "Hello from Anna!"\n  print message')
                    continue
                if c == "env":
                    print(env)
                    continue
                if c == "load" and arg:
                    try:
                        with open(arg, "r", encoding="utf-8") as f:
                            Anna(f.read(), env).run()
                        print(f"Loaded {arg}")
                    except Exception as e:
                        print("Load error:", e)
                    continue
                if c == "reset":
                    env = make_env()
                    print("reset")
                    continue
                print("Unknown command; :help")
                continue
            # non-meta: run single-line program through the same engine
            try:
                Anna(line, env).run()
            except Exception as e:
                print("Error:", e)

# --------------------------
# Alex — tiny imperative
#   - set name = expr   (assign)
#   - print expr
#   - supports full-statement blocks (exec) when needed
# --------------------------
class Alex:
    def __init__(self, source: str, env: Dict[str, Any] | None = None):
        self.lines = source.splitlines()
        self.env = make_env(env)

    def run(self) -> Dict[str, Any]:
        # We'll try to run each line: if it looks like a set/print, handle,
        # otherwise try compile-exec for statements or eval for expressions.
        buffer_lines = []
        for raw in self.lines:
            line = raw.rstrip()
            if not line or line.strip().startswith("#"):
                continue
            # handle set and print as conveniences
            stripped = line.strip()
            if stripped.startswith("set ") and "=" in stripped:
                # set name = expr
                body = stripped[4:]
                name, expr = body.split("=", 1)
                name = name.strip()
                val = eval_expr(expr.strip(), self.env)
                self.env[name] = val
                continue
            if stripped.startswith("print "):
                expr = stripped[len("print "):].strip()
                val = eval_expr(expr, self.env)
                print(val)
                continue
            # For anything else, try to execute as statements (so def/for/while work).
            # If its a single expression, eval will run and return a value (we won't print by default).
            try:
                # Try as a statement first (exec). This allows def, loops, etc.
                exec_stmt(line, self.env)
            except RuntimeError as e_stmt:
                # If exec failed because it's not a statement, try eval
                # (usually exec will raise on invalid syntax only)
                try:
                    _ = eval_expr(line, self.env)
                except Exception as e_eval:
                    # Re-raise the original statement error if both fail
                    raise e_stmt
        return self.env

    @staticmethod
    def repl():
        print("Alex REPL — :help for commands. Use `set name = expr`, `print expr`. You can also type Python statements.")
        env = make_env()
        while True:
            try:
                line = input("alex> ").rstrip()
            except (KeyboardInterrupt, EOFError):
                print(); break
            if not line:
                continue
            if line.startswith(":"):
                cmd = line[1:].strip().split(maxsplit=1)
                c = cmd[0].lower()
                arg = cmd[1] if len(cmd) > 1 else ""
                if c in ("q", "quit", "exit"):
                    break
                if c in ("h", "help"):
                    print("Commands: :help, :examples, :env, :load <file>, :reset, :quit")
                    print("Alex syntax: set name = expr  |  print expr  |  (Python statements supported)")
                    continue
                if c == "examples":
                    print("Example:\n  set add = lambda x,y: x+y\n  set total = add(2,3)\n  print total")
                    continue
                if c == "env":
                    print(env)
                    continue
                if c == "load" and arg:
                    try:
                        with open(arg, "r", encoding="utf-8") as f:
                            Alex(f.read(), env).run()
                        print(f"Loaded {arg}")
                    except Exception as e:
                        print("Load error:", e)
                    continue
                if c == "reset":
                    env = make_env()
                    print("reset")
                    continue
                print("Unknown command; :help")
                continue
            # Non-meta: try to execute as a small program line
            try:
                Alex(line, env).run()
            except Exception as e:
                print("Error:", e)

# --------------------------
# Rosa — simplified scripting (kept consistent)
#   - name := expr
#   - print expr
#   - fact <string> (stores facts as simple strings)
# --------------------------
class Rosa:
    def __init__(self, source: str, env: Dict[str, Any] | None = None):
        self.lines = source.splitlines()
        self.env = make_env(env)
        # facts stored under env['facts'] as a set of strings
        self.env.setdefault("facts", set())

    def run(self) -> Dict[str, Any]:
        for raw in self.lines:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("fact "):
                payload = line[len("fact "):].strip()
                self.env["facts"].add(payload)
                continue
            if ":=" in line:
                name, expr = [p.strip() for p in line.split(":=", 1)]
                val = eval_expr(expr, self.env)
                self.env[name] = val
                continue
            if line.startswith("print "):
                expr = line[len("print "):].strip()
                # print the evaluated expr if it is a Python expression; otherwise raw text
                try:
                    val = eval_expr(expr, self.env)
                except Exception:
                    val = expr
                print(val)
                continue
            # fallback: try to eval as expression (no side-effect)
            try:
                _ = eval_expr(line, self.env)
            except Exception:
                pass
        return self.env

    @staticmethod
    def repl():
        print("Rosa REPL — :help for commands. `fact <text>` records a fact. `print <expr>` prints.")
        env = make_env()
        env.setdefault("facts", set())
        while True:
            try:
                line = input("rosa> ").rstrip()
            except (KeyboardInterrupt, EOFError):
                print(); break
            if not line:
                continue
            if line.startswith(":"):
                cmd = line[1:].strip().split(maxsplit=1)
                c = cmd[0].lower()
                arg = cmd[1] if len(cmd) > 1 else ""
                if c in ("q", "quit", "exit"):
                    break
                if c in ("h", "help"):
                    print("Commands: :help, :examples, :env, :facts, :load <file>, :reset, :quit")
                    print("Rosa syntax: fact some_text  |  name := expr  |  print expr")
                    continue
                if c == "examples":
                    print("Example:\n  fact sky_is_blue\n  print \"Hello from Rosa!\"\n  :env")
                    continue
                if c == "env":
                    print(env)
                    continue
                if c == "facts":
                    print(env.get("facts", set()))
                    continue
                if c == "load" and arg:
                    try:
                        with open(arg, "r", encoding="utf-8") as f:
                            Rosa(f.read(), env).run()
                        print(f"Loaded {arg}")
                    except Exception as e:
                        print("Load error:", e)
                    continue
                if c == "reset":
                    env = make_env()
                    env.setdefault("facts", set())
                    print("reset")
                    continue
                print("Unknown command; :help")
                continue
            # non-meta input runs through the same single-line runner
            try:
                Rosa(line, env).run()
            except Exception as e:
                print("Error:", e)

# --------------------------
# CLI glue
# --------------------------
def main():
    parser = argparse.ArgumentParser(description="Trio of tiny interpreters: anna, alex, rosa")
    parser.add_argument("lang", choices=["anna", "alex", "rosa"], help="language to run")
    parser.add_argument("file", nargs="?", help="program file to run (optional)")
    parser.add_argument("--repl", action="store_true", help="force repl")
    args = parser.parse_args()

    if args.lang == "anna":
        if args.file and not args.repl:
            with open(args.file, "r", encoding="utf-8") as f:
                Anna(f.read()).run()
        else:
            Anna.repl()
    elif args.lang == "alex":
        if args.file and not args.repl:
            with open(args.file, "r", encoding="utf-8") as f:
                Alex(f.read()).run()
        else:
            Alex.repl()
    else:  # rosa
        if args.file and not args.repl:
            with open(args.file, "r", encoding="utf-8") as f:
                Rosa(f.read()).run()
        else:
            Rosa.repl()

if __name__ == "__main__":
    main()
