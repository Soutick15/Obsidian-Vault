# Day 4 — Classes, Type Hints & Pydantic

**Python Foundation Pre-Course · Day 4 of 5**

---

## 1. Learning Objectives

By the end of Day 4 you will be able to:

- Define a class with `__init__`, instance attributes, and methods; distinguish instance vs class attributes
- Convert a plain class to a `@dataclass` and know when each style fits
- Write basic single-level inheritance and override a method
- Annotate variables and function signatures with type hints (`str`, `int`, `list[...]`, `dict[...]`, `Optional` / `X | None`)
- Explain how type hints improve tooling (autocompletion, mypy, IDE warnings) without affecting runtime
- Create a Pydantic v2 `BaseModel`, add fields with defaults and validators, parse a dict into a model, call `model_dump()`, and catch `ValidationError`
- Use a `with` statement to manage resources and write a minimal context manager with `__enter__` / `__exit__`
- Write a simple decorator (timing example) and explain the `@` syntax
- Use `logging` instead of `print` for diagnostic output

---

## 2. Concept Reading

### 2.1 Classes — the basics

A **class** is a blueprint. 
An **object** is an instance built from that blueprint class. 
A class have attributes (variable ) and behaviours (Methods)

```python
class Employee:
	company : str = "Inspiron"
	
	# __init__ is used for constructor
	def __init__(self, name: str, age: int, salary: float, courses: list) -> None :
	self.name = name
	self.age = age
	self. salary = salary
	self.courses = courses

	# represents Sring representation of object
	def __repr__(self) -> str:
		return f"Employee(name='{self.name}', age={self.age}, salary={self.salary}, courses={self.courses})"


# Creating Object of the class
emp1 = Employee("Soutick", 25, 38999.99, ["Java", "Python"])
emp2 = Employee("Munu", 24, 36999.99, ["Javascript", "Go"])

  
print(emp1)    # Employee(name='Soutick', age=25, salary=29999.99....])
print(emp2)    # Employee(name='Munu', age=24, salary=26996.64...])
print(emp1, emp2) # Employee(name='Soutick'....]) Employee(name='Munu'...])
print(Employee.company)  # Inspiron
```

`self` refers to the current object. 
#### 2.1.0 `__init__(self)
`
- `__init__` is used to declare a constructor, it is used for initialising the objects. It runs once when you call `ClassName(...)`.
- Every method receives `self` as the first argument — Python passes the object automatically.
- Class attributes live on the class; instance attributes live on `self`.
- By default default constructor `__init__`is available

#### 2.1.1 `__repr__ (self)` 

- `__repr__`is used to represent an object as a string. Similar like `toString()` method in java
- Without it if you print the object it will print something like this `<__main__.Employee object at 0x10a0e4410>`
- But with `__repr__` it will print the proper string representation 

#### 2.1.2 `__eq__ (self)`

- It is used to compare two objects. Similar like `equals()` method in java

```python
# we create two objects with same value
emp1 = Employee("Soutick", 25, 38999.99, ["Java", "Python"])
emp2 = Employee("Soutick", 25, 38999.99, ["Java", "Python"])

# without `__eq__` method `==` Compares two Memory Address
print(emp1 == emp2) # false
```

```Python
	def __eq__(self, other):
	
	    if not isinstance(other, Employee):
	        return False
	
	    return (
	        self.name == other.name
	        and self.age == other.age
	        and self.salary == other.salary
	        and self.courses == other.courses
	    )
	    
	    
emp1 = Employee("Soutick", 25, 38999.99, ["Java", "Python"])
emp2 = Employee("Soutick", 25, 38999.99, ["Java", "Python"])

# with `__eq__` method `==` Compares value
print(emp1 == emp2) # True
```
---

### 2.2 `@dataclass` — less boilerplate 

`@dataclass` auto-generates `__init__`, `__repr__`, and `__eq__` from the field declarations. No need to declare these explicitly. 

```python
from dataclasses import dataclass, field

@dataclass
class Team:
    name: str
    members: list[str] = field(default_factory=list)  # mutable default

@dataclass
class Employee:
	name: str
	age: int
	salary: float
	courses: list
	
	company : str = "Inspiron"

emp1 = Employee("Soutick", 25, 38999.99, ["Java", "Python"])
emp2 = Employee("Munu", 24, 36999.99, ["Javascript", "Go"])

  
print(emp1) # Employee(name='Soutick'....])
print(emp2) # Employee(name='Munu'...])
print(emp1 == Employee("Soutick", 25, 38999.99, ["Java", "Python"])) # True
```

Use a plain class when you need custom `__init__` logic or properties. Use `@dataclass` for simple data containers.

### static & non static method :

```python
from dataclasses import dataclass

@dataclass
class Employee:
	name: str
	age: int
	company : str = "Inspiron" # field with default

	@staticmethod
	def greet() :
		print("Hello from Static Method")
		  
	def greetByMe(self) :
		print(f"greetings from {self.name}")
		

emp1 = Employee("Soutick", 25)
emp2 = Employee("Munu", 24)

Employee.greet()        # Hello from Static Method
emp1.greetByMe()        # greetings from Soutick
```
### 2.3 OOPs pillers
#### 2.3.0 Encapsulation : Wrapping the  data and methods into a single class.

```python
from dataclasses import dataclass

@dataclass
class Employee:
    name: str
    age: int

    company: str = "Inspiron"

    def introduce(self):
        print(f"Hi, I am {self.name} and I am {self.age} years old.")

emp = Employee("Soutick", 25)
emp.introduce(). # Hi, I am Soutick and I am 25 years old.
```
---
#### 2.3.1 abstraction : Hide the implementation details of a class and show only the essential feature to the user

```python
from dataclasses import dataclass

@dataclass
class Employee:
    name: str
    age: int

    company: str = "Inspiron"

    def calculate_bonus(self):
        return 5000
        
emp = Employee("Soutick", 25)
print(emp.calculate_bonus()). # 5000
```

#### 2.3.2 Inheritance  

```python
class Employee:

    company = "Inspiron"

    def __init__(self, name: str, dept: str, salary: float) -> None:
        self.name = name
        self.dept = dept
        self.salary = salary

	def work(self):
		print(f"Employee {self.name} is working")

    def annual_cost(self) -> float:
        return self.salary * 12
```

```python
class Manager(Employee):

    def __init__(self, name: str, dept: str, salary: int, reports: int) -> None:
        super().__init__(name, dept, salary)
        self.reports = reports
    
    # override the parent calss method
	def work(self):
		print(f"Manager {self.name} is working")


        
```

```python
employee = Employee("Soutick", "BE", 40000.76)
manager = Manager("Raj", "QA", 100000.55, 5)

employee.work()                    # Employee Soutick is working
manager.work()                     # Manager Raj is working

print(employee.annual_cost())      # 480009.12
print(manager.annual_cost())       # 1200006.48
```

---
with `@dataclass`  we can remove the ` super().__init__()` constructor. Python will automatically call ` super().__init__()` internally. 

```python
from dataclasses import dataclass

@dataclass
class Employee:
    name: str
    dept: str
    salary: float

    company = "Inspiron"

    def work(self):
        print(f"Employee {self.name} is working")

    def annual_cost(self) -> float:
        return self.salary * 12


@dataclass
class Manager(Employee):

    reports: int

    def work(self):
        print(f"Manager {self.name} is working")
```


**When to inherit:** when the child *is a* specialisation of the parent and needs its interface. Prefer composition (holding an object) over inheritance when you just need to *use* a class.


#### 2.3.3 Polymorphism


```python
from dataclasses import dataclass

@dataclass
class Employee:
    name: str
    age: int

    company: str = "Inspiron"

    def calculate_bonus(self):
        return 5000
        
emp = Employee("Soutick", 25)
print(emp.calculate_bonus())
```




### 2.4 Type hints

Type hints describe what types a variable or function expects. Python does **not** enforce them at runtime — they help your editor, linters, and teammates.

```python
# Variable annotations
age: int = 30
tags: list[str] = ["python", "ai"]
scores: dict[str, float] = {"math": 9.5}

# Function annotations
def add(a: int, b: int) -> int:
    return a + b

# Optional — value is str OR None
from typing import Optional

def find_user(uid: int) -> Optional[str]:
    users = {1: "Alice"}
    return users.get(uid)

# Python 3.10+ shorthand (preferred in new code)
def find_user_v2(uid: int) -> str | None:
    ...
```

**Why they matter for AI work:** LLM output parsers, prompt builders, and tool-use schemas all rely on type information to generate and validate structured data.

### 2.5 Pydantic v2 — validated data models

Pydantic is the most widely used data validation library in Python. It is the backbone of structured LLM output in frameworks like LangChain, LlamaIndex, and the Anthropic Python SDK's tool-use helpers.

```python
import re
from pydantic import BaseModel, field_validator, ValidationError

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

class Employee(BaseModel):
    name: str
    dept: str
    salary: int
    email: str

    @field_validator("salary")
    @classmethod
    def salary_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("salary must be > 0")
        return v

    @field_validator("email")
    @classmethod
    def email_valid(cls, v: str) -> str:
        if not _EMAIL_RE.match(v):
            raise ValueError("value is not a valid email address")
        return v

# Parse a dict into the model
data = {"name": "Priya", "dept": "Engineering", "salary": 80_000, "email": "priya@co.com"}
emp = Employee(**data)          # or Employee.model_validate(data)
print(emp.name)                 # Priya
print(emp.model_dump())         # {'name': 'Priya', 'dept': 'Engineering', ...}

# ValidationError when data is wrong
bad = {"name": "X", "dept": "HR", "salary": -500, "email": "not-an-email"}
try:
    Employee(**bad)
except ValidationError as e:
    print(e)   # lists every field error with location + message
```

Key Pydantic v2 facts:
- Fields are declared as class-level annotations (no `__init__` needed).
- Validation runs automatically on construction.
- `model_dump()` returns a plain `dict` (was `.dict()` in v1).
- `model_dump(mode="json")` serialises to JSON-compatible types.
- `model_validate(dict)` is the explicit way to parse from a dict.

### 2.6 Context managers (`with`)

Context managers guarantee that setup and teardown code runs — even if an exception is raised.

```python
# Built-in example: file handles
with open("notes.txt", "w") as fh:
    fh.write("hello")
# fh is closed automatically here

# Writing your own
import time

class Timer:
    """Self-contained timer — records start in __enter__, prints elapsed in __exit__."""

    def __enter__(self):
        self._start = time.perf_counter()
        return self             # value bound to `as` variable

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.perf_counter() - self._start
        print(f"Elapsed: {self.elapsed:.4f}s")
        return False            # don't suppress exceptions

with Timer() as t:
    total = sum(range(1_000_000))
# prints: Elapsed: 0.0312s  (caller sets nothing on t; Timer handles it all)
```

### 2.7 Decorators — a brief intro

A decorator is a function that wraps another function to add behaviour.

```python
import time
import functools

def timed(func):
    @functools.wraps(func)      # preserves __name__, __doc__
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.perf_counter() - start:.4f}s")
        return result
    return wrapper

@timed                          # equivalent to: slow = timed(slow)
def slow():
    time.sleep(0.1)
    return "done"

slow()   # slow took 0.1003s
```

The `@` line is pure syntactic sugar — nothing more.

### 2.8 `logging` vs `print`

`print` is for user-facing output. `logging` is for diagnostic messages that can be turned on/off by level and redirected to files.

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

logger.debug("entering parse_response()")
logger.info("model returned %d tokens", 512)
logger.warning("rate limit approaching")
logger.error("validation failed: %s", "missing field")
```

In production code (including AI pipelines), set the level to `WARNING` or higher so debug noise is silenced without removing the statements.

---

## 3. Hands-on Exercise

The exercise lives in `curriculum/python-foundation/exercises/day-04/`.

**Files:**
- `starter.py` — complete every `# TODO` block
- `solution.py` — reference implementation (check only after attempting)

**Tasks:**
1. Define a `@dataclass` called `Department` with `name` and `headcount` fields.
2. Define a Pydantic `Employee` model with validated fields; parse a valid dict and print `model_dump()`; catch `ValidationError` from an invalid dict.
3. Use a `with` statement to time a computation using the `Timer` context manager from the reading.
4. Verify your output matches the expected output comments in `starter.py`.

**Setup** (run once from the repo root):
```bash
pip install -r curriculum/python-foundation/exercises/requirements.txt
```

**Run:**
```bash
python curriculum/python-foundation/exercises/day-04/starter.py
```

---

## 4. Self-Check Quiz

**Q1. What is the difference between a class attribute and an instance attribute?**

<details>
<summary>Show answer</summary>

A class attribute is defined directly on the class body and is shared by every instance. An instance attribute is set via `self.attr = value` inside a method (typically `__init__`) and belongs only to that specific object. Assigning to `self.attr` on an instance hides the class attribute for that instance but leaves other instances unaffected.

</details>

**Q2. What does `@dataclass` auto-generate that saves you writing boilerplate?**

<details>
<summary>Show answer</summary>

`@dataclass` generates `__init__` (accepting each annotated field as a parameter), `__repr__` (a readable string representation), and `__eq__` (equality by field values). Optional flags like `order=True` also generate comparison methods (`__lt__`, etc.) and `frozen=True` makes instances immutable.

</details>

**Q3. Do Python type hints affect runtime behaviour?**

<details>
<summary>Show answer</summary>

No. Python's interpreter ignores annotations at runtime (they are stored in `__annotations__` but not enforced). Type hints only matter to static analysis tools — mypy, pyright, IDE autocompletion — and to libraries like Pydantic that explicitly read them. You can pass the wrong type at runtime and Python will not raise an error unless the called code itself checks.

</details>

**Q4. What is `Optional[str]` equivalent to in Python 3.10+ syntax?**

<details>
<summary>Show answer</summary>

`str | None`. Both express that a value is either a `str` or `None`. The newer union syntax (`X | Y`) is preferred in Python 3.10+ because it is more concise and does not require importing `Optional` from `typing`.

</details>

**Q5. What does Pydantic's `ValidationError` contain?**

<details>
<summary>Show answer</summary>

A `ValidationError` contains a list of error details, one per field that failed validation. Each entry includes the field location (e.g., `['salary']`), the error type (e.g., `value_error`), and a human-readable message. You can iterate `e.errors()` to get a list of dicts, or call `str(e)` for a formatted summary.

</details>

**Q6. What is the purpose of `__enter__` and `__exit__` in a context manager?**

<details>
<summary>Show answer</summary>

`__enter__` runs when the `with` block is entered; its return value is bound to the `as` variable. `__exit__` runs when the block exits — whether normally or due to an exception. It receives the exception type, value, and traceback as arguments; returning `True` suppresses the exception, returning `False` (or `None`) lets it propagate.

</details>

**Q7. What does `@functools.wraps(func)` do inside a decorator?**

<details>
<summary>Show answer</summary>

It copies the wrapped function's `__name__`, `__doc__`, `__module__`, and `__qualname__` onto the `wrapper` function. Without it, every decorated function would appear to have the name `wrapper`, which breaks introspection, debugging, and tools that rely on `__name__`.

</details>

**Q8. Why use `logging` instead of `print` in application code?**

<details>
<summary>Show answer</summary>

`logging` provides severity levels (DEBUG, INFO, WARNING, ERROR, CRITICAL) so you can filter output without deleting statements. It supports multiple handlers (console, file, remote) simultaneously, includes timestamps and caller info automatically, and can be configured globally — useful in larger programs and AI pipelines where you want fine-grained control over what appears in production logs.

</details>

---

## 5. Concept Deep-Dive Q&A

**Q1. Why does Pydantic matter for structured LLM outputs, and how does a `BaseModel` connect to that use case?**

<details>
<summary>Show answer</summary>

LLMs return text. When you need structured data — a JSON object with specific fields, validated types, and constraints — you must parse and validate that text. Pydantic `BaseModel` subclasses serve as a schema: you declare the expected shape once, and Pydantic validates the parsed JSON against it. Frameworks like LangChain's output parsers and the Anthropic SDK's tool-use layer accept a `BaseModel` subclass to auto-generate a JSON Schema for the model's tool definition and then validate the returned arguments. This means a single class declaration replaces manual schema writing, manual validation, and manual type-casting.

</details>

**Q2. What is the MRO (Method Resolution Order) and why does it matter in inheritance?**

<details>
<summary>Show answer</summary>

The MRO is the order in which Python searches base classes when resolving a method or attribute name. It is computed using the C3 linearisation algorithm and stored in `ClassName.__mro__`. In single inheritance it is simply child → parent → grandparent → `object`. In multiple inheritance (e.g., `class C(A, B)`) the MRO decides which parent's method wins when both define the same name. `super()` follows the MRO, so it does not always mean "the direct parent" — it means "the next class in the MRO." Understanding this prevents subtle bugs in cooperative multiple inheritance.

</details>

**Q3. How does Pydantic v2 differ from v1, and what are the most common migration pitfalls?**

<details>
<summary>Show answer</summary>

Pydantic v2 rewrote its core in Rust (via `pydantic-core`), making it roughly 5–50× faster. Key API changes:
- `.dict()` → `.model_dump()`; `.json()` → `.model_dump_json()`
- `.parse_obj()` → `.model_validate()`; `.parse_raw()` → `.model_validate_json()`
- `@validator` → `@field_validator` with `@classmethod`
- `class Config` → `model_config = ConfigDict(...)`
- Field metadata moved to `Field(...)` keyword arguments rather than `Schema`.

Common pitfalls: forgetting `@classmethod` on `@field_validator`; using v1 `validator` which silently does nothing in v2; and relying on `orm_mode = True` which is now `from_attributes = True` in `ConfigDict`.

</details>

**Q4. What is the difference between composition and inheritance, and when should you prefer each?**

<details>
<summary>Show answer</summary>

Inheritance models an "is-a" relationship: a `Manager` *is an* `Employee`. Composition models a "has-a" relationship: a `Team` *has a* list of `Employee` objects. Prefer composition when:
- The child does not truly satisfy the parent's full interface (Liskov Substitution Principle violation).
- You need to swap implementations at runtime.
- You want to reuse behaviour from multiple unrelated classes (inheritance becomes a diamond-problem tangle).

Prefer inheritance when the subtype genuinely extends the parent's contract and the hierarchy is shallow (typically ≤ 2–3 levels). In AI framework code you will often see composition: a `ChatBot` class *holds* a `MemoryStore` and a `PromptBuilder` rather than inheriting from either.

</details>

**Q5. How do decorators work mechanically — what exactly happens at import time vs call time?**

<details>
<summary>Show answer</summary>

At **import time** (when the module is loaded), Python evaluates the decorator expression and replaces the decorated name with the result. So `@timed` on `def slow(): ...` executes `slow = timed(slow)` immediately — `slow` is now the `wrapper` function. At **call time**, whenever you call `slow()`, you are calling `wrapper()`, which runs the timing logic, delegates to the original function, and returns its result. Decorators that accept arguments (e.g., `@retry(times=3)`) add one more level: the outer callable returns the actual decorator, which then wraps the function.

</details>

**Q6. What are `model_dump()` and `model_dump(mode="json")` in Pydantic v2, and when would you use each?**

<details>
<summary>Show answer</summary>

`model_dump()` returns a Python `dict` with native Python types — `datetime` objects stay as `datetime`, `UUID` stays as `UUID`. This is ideal when you need to pass the data to other Python code. `model_dump(mode="json")` serialises to JSON-compatible types — `datetime` becomes an ISO string, `UUID` becomes a string, `Decimal` becomes a string or float depending on config. Use `mode="json"` when you are about to call `json.dumps()` or pass the dict to an HTTP client that expects JSON-serialisable data. There is also `model_dump_json()` which returns a `str` directly without an intermediate `dict`.

</details>

**Q7. Why are mutable default arguments dangerous in plain classes and how does `dataclasses.field(default_factory=...)` solve it?**

<details>
<summary>Show answer</summary>

In Python, default argument values are evaluated once at function-definition time, not each time the function is called. If you write `def __init__(self, items=[])`, all instances share the *same* list object. Appending to `self.items` on one instance mutates every other instance's list too. `@dataclass` detects mutable defaults (list, dict, set) and raises a `ValueError` if you set them directly as field defaults, forcing you to use `field(default_factory=list)` instead. The factory is called fresh for each new instance, giving each its own independent list.

</details>

**Q8. How does the `logging` hierarchy work and why does using `getLogger(__name__)` matter?**

<details>
<summary>Show answer</summary>

Python loggers form a tree rooted at the root logger. A logger named `myapp.models` is a child of `myapp`, which is a child of the root. Log records propagate up the tree by default, so setting the level or handler on a parent logger affects all its children. `getLogger(__name__)` creates a logger named after the current module (e.g., `curriculum.day4`). This means:
1. You can silence a noisy third-party library by disabling its top-level logger without affecting your own code.
2. You can enable debug logging for just one package (`logging.getLogger("myapp.parsers").setLevel(logging.DEBUG)`) while keeping others quiet.
3. Log records automatically show which module emitted the message, making large-application debugging much easier.

</details>

---

## 6. Key Takeaways

- **Classes** bundle data (attributes) and behaviour (methods). `self` gives each instance access to its own data; class attributes are shared.
- **`@dataclass`** removes `__init__`/`__repr__`/`__eq__` boilerplate for plain data containers; use `field(default_factory=...)` for mutable defaults.
- **Inheritance** is powerful but should be used sparingly — prefer "is-a" relationships, keep hierarchies shallow, and consider composition first.
- **Type hints** cost nothing at runtime but pay dividends in IDE support, refactoring safety, and documentation. Use `X | None` (Python 3.10+) or `Optional[X]` for nullable values.
- **Pydantic v2** provides fast, declarative data validation. `BaseModel` subclasses are the standard way to describe and validate structured data in modern Python AI code — LLM tool-use schemas, API response parsing, and config loading all use this pattern.
- **Context managers** (`with`) guarantee cleanup. Write your own via `__enter__` / `__exit__` when you need reliable setup/teardown around a resource or timed block.
- **Decorators** wrap functions to add cross-cutting concerns (timing, logging, retry, auth). Always use `@functools.wraps` to preserve the original function's metadata.
- **`logging`** beats `print` for diagnostic output: it is filterable by level, redirectable, and self-documenting. Use `getLogger(__name__)` in every module.
