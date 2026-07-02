# Day 1 — Running Python and the Basics

---

## 1. Learning Objectives

By the end of Day 1 you will be able to:

1. Explain what Python is, how the interpreter executes a script, and where to get help when something breaks.
2. Create and activate a virtual environment, install packages with `pip`, and run a Python script from the terminal.
3. Use the Python REPL for quick experiments and know when to prefer it over a file.
4. Declare variables with Python's core types (`int`, `float`, `str`, `bool`, `None`), use operators, and build readable strings with f-strings.
5. Control program flow with `if/elif/else`, `for`, `while`, `range`, `break`, and `continue`, and guard a script's entry point with `if __name__ == "__main__":`.

---

## 2. Concept Reading

### 2.1 What Python Is and How It Runs

Python is an interpreted, dynamically-typed, general-purpose language first released in 1991. "Interpreted" means there is no separate compile step — you hand your source file to the **Python interpreter**, which reads it line by line and executes it immediately. (Under the hood, CPython does compile your source to bytecode — the `.pyc` files you'll see in `__pycache__/` — but this happens automatically and invisibly; there is no manual compile command you need to run.)

```
your_script.py  →  [Python interpreter]  →  output
```

The interpreter ships as the `python` (or `python3`) binary. On most systems:

```bash
python3 --version      # confirm Python is installed
Python 3.14.6          # output

python3 my_script.py   # run a file
```

When something goes wrong Python prints a **traceback** — read it bottom-up. The last line tells you *what* went wrong; the lines above show *where* it happened.

```bash
Traceback (most recent call last):
  File "my_script.py", line 4, in <module>
    print(namee)         # <-- line 4 in your file
NameError: name 'namee' is not defined
```

Quick debugging tip: add `print()` calls around the broken line to inspect values before the crash.

---

### 2.2 Virtual Environments and pip

A **virtual environment** (venv) is an isolated Python installation. Every lab in this course uses one so that packages installed for one lab do not interfere with another.

```bash
# Create a venv named .venv in the current directory
python3 -m venv .venv

# Activate it — macOS / Linux
source .venv/bin/activate

# Activate it — Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Your prompt now shows (.venv)
# Install a package
pip install requests

# List installed packages
pip list

# Deactivate when done
deactivate
```

`pip install -r requirements.txt` installs every package listed in a requirements file — this is what the lab `setup/` scripts use.

---

### 2.3 Script vs REPL

| | Script (`python file.py`) | REPL (`python3` with no file) |
|---|---|---|
| Best for | repeatable, shareable work | quick experiments, checking a type |
| Runs | top to bottom, then exits | line by line, stays open |
| State | fresh each run | accumulates across entries |

Start the REPL by typing `python3` at your terminal prompt. Exit with `exit()` or Ctrl-D.

```python
>>> 2 ** 10
1024
>>> type("hello")
<class 'str'>
```

---

### 2.4 Variables and Core Types


Data types in Python : Python has total 5 primitive data type

```python
str
float
int
bool
NoneType
```

Python variables are **labels** attached to objects. You do not declare a type — the interpreter infers it.

```python
count   = 42          # int
price   = 3.99        # float
name    = "Ada"       # str
active  = True        # bool  (True / False — capital first letter)
result  = None        # None  (the absence of a value)
```

Check the type of anything with `type()` and the identity with `isinstance()`:

```python
>>> type(count)
<class 'int'>
>>> isinstance(active, bool)
True
```

**Truthiness** — every value has a boolean meaning. The following are **falsy**: `0`, `0.0`, `""`, `[]`, `{}`, `None`, `False`. Everything else is truthy.

```python
if count:          # True because count = 42 (non-zero)
    print("non-zero")
```

---

### 2.5 Operators

Arithmetic Operators 

```python
10 + 3   # 13
10 - 3   # 7
10 * 3   # 30
10 / 3   # 3.3333...  (always float)
10 // 3  # 3          (integer division, floor; returns int when both operands are int)
7.0 // 2 # 3.0        (// returns a float when either operand is a float)
10 % 3   # 1          (remainder)
2 ** 8   # 256        (exponentiation)

```

 Comparison Operator — return bool (true / false) : `>` , `<` , `==` , `>=` , `<=` , `!=`

```python
5 > 3    # True
5 == 5   # True  (equality, not assignment)
5 != 4   # True
```

 Logical operators : `and` , `or` , `not`

```python

True and False   # False
True or False    # True
not True         # False
not False        # True
```
---

### 2.6 Strings and f-strings

Strings are sequences of Unicode characters. 
We can declare strings with 
	single quotes `' ' ` 
	double quotes `" "`  
	triple quotes `""" """`

```python
greeting = "Hello world!"
name     = 'Namaste Duniya!'
name2    = """ Hello India !"""
```

String Concatenation : 

```python

greeting = "Hello"
name = 'Soutick'
Address = """Bengaluru"""

# Concatenation
message = greeting + ", " + name + "!"
message2 = "welcome to " + Address + "!"

print (message) # Hello, Soutick!
print (message2) # welcome to Bengaluru!

```

instead of concatenation multiple times we can use f-string


```python
greeting = "Hello"
name = 'Soutick'
Address = """Bengaluru"""
score = 97
  
# f-strings (Python 3.6+) — put an f before the quote

# Hello ! Soutick, welcome to Bengaluru
print (f"{greeting} ! {name}, welcome to {Address}") 

  
print(f"Score: {score}/100") # Score: 97/100
print(f"Upper: {name.upper()}") # Upper: SOUTICK
print(f"Length: {len(greeting)}") # Length: 5

```

Useful string methods: `.split()`, `.strip()`, `.lower()`, `.upper()`, `.replace()`, `.startswith()`.

---

### 2.7 print() and input()

```python

greeting = "Hello"
name = 'Soutick'
Address = """Bengaluru"""
score = 97

print("Hello")                     # Hello
print("a", "b", "c")               # a b c  (space-separated by default)
print("a", "b", sep="-")           # a-b
print("loading", end="...")        # loading...  (no newline)
print (greeting,",", "welcome to", Address) #Hello , welcome to Bengaluru

```

`input()` : Used to take some input value from the user, always returns a **string** by default. Even if you enter a number, it will internally convert it into a string value. Always  Convert it according to your requires data type :

```python
name = input("Enter Your name: ")  # blocks until user presses Enter
age = int(input("Age: "))          # taking a input value of int type 
salary = float(input("Salary: "))  # taking a input value of float type 

# Hi, SOUTICK!
print(f"Hi, {name}!") 

# Your age is 25 and your salary is 35000.0!
print (f"Your age is {age} and your salary is {salary}!") 
```

---

### 2.8 Comments

```python
# This is a single-line comment — Python ignores everything after #

x = 5  # inline comment — fine to explain a non-obvious value
```

Multi-line strings (triple quotes) are sometimes used as block comments, but proper `#` comments are preferred for readability.

---

### 2.9 Control Flow

#### if / elif / else

```python

temperature = 26

if temperature > 40:
	print("Very Hot")
	print("Use AC")

elif temperature > 30:
	print("Hot")
	print("Use Cooler")

elif temperature >20: # <-- condition matched
	print("Warm")     # <-- this runs
	print("Use Fan")  # <-- this runs

else:
	print("Cold")
	print("Use Blanket")

print("Thank You") # <-- this runs
```

Python uses **indentation** (4 spaces by convention) instead of braces to define blocks `{}`, indentation is used to group multiple statements together.

#### for and range()

```python
# start = 0 (default), end = 5
for i in range(5):          # 0, 1, 2, 3, 4
    print(i)
```


```python
name = "Hello"

for i in range(len(name)): # H, e , l, l,  o
	print(name[i])
```


```python
fruits = ["apple", "banana", "cherry"]

# Iterate Using Index
for i in range(len(fruits)):
	print (fruits[i])            # apple banana cherry

 # Iterate Over Values (Used When we only need the values)
for i in fruits:
    print(i.upper())              # APPLE BANANA CHERRY
   

# This will print the `i` values only
for i in range(len(fruits)):
	print (i)                 # 0 1 2 3 4
    
    
```


#### `range(start, stop, step)` — `stop` is exclusive & mandatory

`range(optiona, mandatory, optional)` 


```python

# start = 0, end = 5, steps = 1
for i in range(5):       # 0 1 2 3 4
	print(i)
	
# ------------------

# # start = 5, end = 10, steps = 1
for i in range(5, 10):
	print(i) # 5 6 7 8 9

# ------------------

# start = 2, end = 10, steps = 2
for i in range(2, 10, 2): # 2, 4, 6, 8
	print(i)

```

for with else :

```Python

fruits = ["apple", "banana", "cherry"]
# Iterate Over Values (Used When we only need the values)

for fruit in fruits:
	if (fruit == "banana"):
		print(fruit)
		break
		
else :
	print("End")
```

---
#### while

```python
count = 0
while count < 3:
    print(f"count = {count}")
    count += 1
```

#### break and continue

```python
for n in range(10):
    if n == 5:
        break           # exit the loop entirely
    if n % 2 == 0:
        continue        # skip to next iteration
    print(n)            # prints 1, 3
```

---

### 2.10 The `if __name__ == "__main__":` Pattern

When Python runs a file directly, it sets the special variable `__name__` to `"__main__"`. When the same file is *imported* as a module, `__name__` is set to the module name instead.

```python
def greet(name):
    return f"Hello, {name}!"

def main():
    print(greet("Ada"))

if __name__ == "__main__":
    main()
```

**Why this matters for labs:**
- You can import helper functions from a lab file without accidentally running its full script.
- Tests and the course grader import your file — they do not want `main()` to fire on import.
- It makes the entry point explicit and easy to find.

---

## 3. Hands-on Exercise

Exercise files live in `exercises/day-01/`.

| File                           | Purpose                                     |
| ------------------------------ | ------------------------------------------- |
| `exercises/day-01/starter.py`  | Your working file — complete every `TODO`   |
| `exercises/day-01/solution.py` | Reference solution — check after you finish |

**Task — Text Stats Tool**

Complete the functions in `starter.py` so that, given the hardcoded `PASSAGE` string, the script prints:

- Line count
- Word count
- Longest word
- Words per starting letter (only letters that appear, sorted A-Z)

All logic must use loops, conditionals, f-strings, and a `main()` guarded by `if __name__ == "__main__":`. No external libraries — stdlib only.

**Run your solution:**

```bash
python exercises/day-01/starter.py
```

Expected output shape (values will match the passage):

```
=== Text Stats ===
Line count  : 5
Word count  : 51
Longest word: garbage-collected

Words per starting letter:
  A : 5
  ...
```

---

## 4. Self-Check Quiz

**Q1. What does the Python interpreter do with your `.py` file?**

<details>
<summary>Show answer</summary>

It reads the file top-to-bottom and executes each statement immediately — there is no separate compilation step that produces a binary. CPython does automatically compile source to bytecode (`.pyc` files stored in `__pycache__/`) before running, but this happens invisibly with no manual step required.

</details>

**Q2. You run `python3 app.py` and see the error below. Which line do you fix first, and what is wrong?**

```
Traceback (most recent call last):
  File "app.py", line 7, in <module>
    print(massage)
NameError: name 'massage' is not defined
```

<details>
<summary>Show answer</summary>

Fix line 7 in `app.py`. The variable is misspelled — it should be `message`, not `massage`. Python is case- and spelling-sensitive: referencing a name that was never assigned raises `NameError`.

</details>

**Q3. What is the difference between `/` and `//` in Python?**

<details>
<summary>Show answer</summary>

`/` always returns a `float` (e.g., `7 / 2` → `3.5`). `//` performs floor division and returns an `int` when **both** operands are integers (e.g., `7 // 2` → `3`), but returns a `float` when either operand is a float (e.g., `7.0 // 2` → `3.0`).

</details>

**Q4. What does `input()` always return, and why does that matter?**

<details>
<summary>Show answer</summary>

`input()` always returns a `str`, even if the user types a number. If you need to do arithmetic with the value you must convert it explicitly: `age = int(input("Age: "))`.

</details>

**Q5. Which of the following values are falsy in Python? `0`, `1`, `""`, `"0"`, `[]`, `None`, `False`**

<details>
<summary>Show answer</summary>

Falsy (among others): `0`, `""`, `[]`, `None`, `False` — as well as `0.0`, `()`, `{}`, and `set()`. Truthy: `1`, `"0"` (non-empty string). The string `"0"` contains a character, so it is truthy even though its content looks like zero.

</details>

**Q6. What is the purpose of `if __name__ == "__main__":`?**

<details>
<summary>Show answer</summary>

It guards code that should run only when the file is executed directly, not when it is imported as a module. When Python runs a file directly it sets `__name__` to `"__main__"`; on import it is set to the module's own name. The guard prevents side-effects (like printing or starting a process) when another file imports your functions.

</details>

**Q7. Rewrite this concatenation as an f-string: `"Hello, " + name + "! You are " + str(age) + " years old."`**

<details>
<summary>Show answer</summary>

```python
f"Hello, {name}! You are {age} years old."
```

No need to call `str()` — f-strings automatically convert the value inside `{}` to its string representation.

</details>

**Q8. What does `range(2, 10, 3)` produce?**

<details>
<summary>Show answer</summary>

The values `2, 5, 8`. `range(start, stop, step)` starts at `2`, increments by `3` each time, and stops before reaching `10`.

</details>

---

## 5. Concept Deep-Dive Q&A

**Q1. Python is called "dynamically typed." What does that mean, and what are the practical trade-offs?**

<details>
<summary>Show answer</summary>

Dynamic typing means the type of a variable is determined at runtime by the value assigned to it, not by a declaration in the source code. The same name can hold an `int` now and a `str` later.

Trade-offs:

- **Pro:** Less boilerplate, faster to prototype, flexible data structures.
- **Con:** Type errors surface at runtime instead of at a compile step, which can make large codebases harder to maintain. This is why the course labs use **type hints** (`def greet(name: str) -> str:`) and tools like `mypy` for optional static checking.

</details>

**Q2. What actually happens on disk when you create a virtual environment with `python3 -m venv .venv`?**

<details>
<summary>Show answer</summary>

Python copies (or symlinks) the interpreter binary into `.venv/bin/` and creates a private `site-packages/` directory inside `.venv/lib/`. When you activate the venv, your shell prepends `.venv/bin/` to `PATH`, so `python` and `pip` resolve to the venv copies. Packages installed with `pip` land in the venv's `site-packages` and are invisible to the system Python — this is the isolation mechanism.

</details>

**Q3. Why does Python use indentation to define blocks instead of curly braces?**

<details>
<summary>Show answer</summary>

This was an explicit design choice by Guido van Rossum to enforce a consistent visual structure. Because indentation is syntactically meaningful, all Python code looks similar regardless of who wrote it — the layout you see in the editor is the layout the interpreter uses to understand nesting. The downside is that mixing tabs and spaces causes `IndentationError`; most editors are configured to convert tabs to 4 spaces automatically.

</details>

**Q4. What is the difference between `=`, `==`, and `is` in Python?**

<details>
<summary>Show answer</summary>

- `=` — assignment. Binds a name to an object: `x = 5`.
- `==` — equality. Compares the *values* of two objects: `5 == 5` is `True`.
- `is` — identity. Compares whether two names point to the *same object in memory*: `a is b`. For small integers and interned strings CPython caches objects, so `a is b` can be `True` unexpectedly. Use `==` for value comparison and `is` only to test against singletons like `None` (`if result is None:`).

</details>

**Q5. When would you use `while` instead of `for`, and how do you avoid an infinite loop?**

<details>
<summary>Show answer</summary>

Use `while` when the number of iterations is not known in advance — for example, reading lines until a blank line is entered, retrying a failing operation, or driving a game loop. Use `for` when iterating over a known sequence or a fixed range.

To avoid an infinite loop: make sure the loop's condition can eventually become `False`, and prefer a safety counter or timeout for loops that depend on external input. Adding a `break` for an emergency exit condition is also common practice.

</details>

**Q6. What is the difference between `break` and `continue`?**

<details>
<summary>Show answer</summary>

`break` exits the **entire loop** immediately — no further iterations run. `continue` skips the **rest of the current iteration** and jumps back to the loop condition (or the next item in a `for` loop). Both affect only the innermost enclosing loop.

```python
for n in range(10):
    if n == 5:
        break       # stops at 5, never prints 5 or higher
    if n % 2 == 0:
        continue    # skips even numbers
    print(n)        # prints 1, 3
```

</details>

**Q7. Why should `input()` never be used in library functions, and what is the better pattern?**

<details>
<summary>Show answer</summary>

`input()` blocks execution and ties your function to a terminal. Functions that contain `input()` cannot be called from automated tests, pipelines, or other scripts. The better pattern is to accept values as **parameters** and call `input()` only in `main()` or at the outermost layer:

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"

def main():
    name = input("Name: ")
    print(greet(name))
```

This keeps logic pure and testable.

</details>

**Q8. What information does a Python traceback give you, and in what order should you read it?**

<details>
<summary>Show answer</summary>

A traceback is a stack of call frames printed when an unhandled exception occurs. Read it **bottom-up**:

1. **Last line** — the exception type and message: tells you *what* went wrong.
2. **Line just above** — the exact file name, line number, and source line: tells you *where* the error occurred.
3. **Lines further up** — the chain of function calls that led to the error: helps you understand *why* execution reached that point.

Start your fix at the bottom. Once you understand the immediate error, scan upward to understand the call path that caused it.

</details>

---

## 6. Key Takeaways

- Python executes scripts line-by-line through the interpreter; read tracebacks bottom-up to find errors fast.
- Always use a virtual environment (`python3 -m venv .venv`) and activate it before installing packages.
- The REPL is ideal for quick experiments; `.py` files are for repeatable, shareable work.
- Core types (`int`, `float`, `str`, `bool`, `None`) are assigned without declarations; use f-strings for readable string formatting.
- `if/elif/else`, `for`, `while`, `range`, `break`, and `continue` cover all everyday control flow needs.
- Guard script entry points with `if __name__ == "__main__":` — this is required in every lab.
