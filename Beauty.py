import sys

# =====================
# Base Help
# =====================
HELP_TEXT = """
Commands (prefix with : )
  :help        Show help
  :examples    Show small demo programs
  :env         Show current variables
  :quit        Exit REPL
"""

# =====================
# Anna Interpreter
# =====================
class Anna:
    def __init__(self, code, env=None):
        self.code = code.strip().splitlines()
        self.env = env if env is not None else {}

    def run(self):
        for line in self.code:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":=" in line:
                name, expr = map(str.strip, line.split(":=", 1))
                self.env[name] = eval(expr, {}, self.env)
            elif line.startswith("print"):
                expr = line[len("print"):].strip()
                print(eval(expr, {}, self.env))
            else:
                # just evaluate expression
                eval(line, {}, self.env)

def repl_anna():
    print("Anna REPL — type :help for help, :quit to exit")
    env = {}
    while True:
        try:
            line = input("anna> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line.startswith(":"):
            cmd = line[1:]
            if cmd == "help":
                print(HELP_TEXT)
                print("Anna syntax: name := expr | print expr")
            elif cmd == "examples":
                print("Example:\n  x := 42\n  print x")
            elif cmd == "env":
                print(env)
            elif cmd == "quit":
                break
            continue
        try:
            Anna(line, env).run()
        except Exception as e:
            print("Error:", e)

# =====================
# Alex Interpreter
# =====================
class Alex:
    def __init__(self, code, env=None):
        self.code = code.strip().splitlines()
        self.env = env if env is not None else {}

    def run(self):
        for line in self.code:
            line = line.strip()
            if not line:
                continue
            if line.startswith("set "):
                name, expr = line[4:].split("=", 1)
                self.env[name.strip()] = eval(expr.strip(), {}, self.env)
            elif line.startswith("print"):
                expr = line[len("print"):].strip()
                print(eval(expr, {}, self.env))
            else:
                eval(line, {}, self.env)

def repl_alex():
    print("Alex REPL — type :help for help, :quit to exit")
    env = {}
    while True:
        try:
            line = input("alex> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line.startswith(":"):
            cmd = line[1:]
            if cmd == "help":
                print(HELP_TEXT)
                print("Alex syntax: set name = expr | print expr")
            elif cmd == "examples":
                print("Example:\n  set x = 7\n  print x * 3")
            elif cmd == "env":
                print(env)
            elif cmd == "quit":
                break
            continue
        try:
            Alex(line, env).run()
        except Exception as e:
            print("Error:", e)

# =====================
# Rosa Interpreter
# =====================
class Rosa:
    def __init__(self, code, env=None):
        self.code = code.strip().splitlines()
        self.env = env if env is not None else {}

    def run(self):
        for line in self.code:
            line = line.strip()
            if not line:
                continue
            if line.startswith("fact "):
                fact = line[5:]
                self.env.setdefault("facts", set()).add(fact)
            elif line.startswith("print"):
                expr = line[len("print"):].strip()
                print(expr)
            else:
                pass

def repl_rosa():
    print("Rosa REPL — type :help for help, :quit to exit")
    env = {"facts": set()}
    while True:
        try:
            line = input("rosa> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line.startswith(":"):
            cmd = line[1:]
            if cmd == "help":
                print(HELP_TEXT)
                print("Rosa syntax: fact something | print message")
            elif cmd == "examples":
                print("Example:\n  fact hello\n  print Hello, world!")
            elif cmd == "env":
                print(env)
            elif cmd == "quit":
                break
            continue
        try:
            Rosa(line, env).run()
        except Exception as e:
            print("Error:", e)

# =====================
# Main
# =====================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python trio_langs.py [anna|alex|rosa]")
        sys.exit(1)

    mode = sys.argv[1]
    if mode == "anna":
        repl_anna()
    elif mode == "alex":
        repl_alex()
    elif mode == "rosa":
        repl_rosa()
    else:
        print("Unknown mode:", mode)
