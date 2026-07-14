# Day 2 — Data Structures & Functions

**Module:** Python Foundation Pre-Course
**Prerequisites:** Day 1 (basics, running scripts, virtual environments)

---

## 1. Learning Objectives

By the end of Day 2 you will be able to:

- Choose the right built-in data structure (list, tuple, dict, set) for a given problem.
- Index, slice, and iterate over sequences using `for`, `enumerate`, `zip`, and `dict.items()`.
- Write list, dict, and set comprehensions to replace verbose loops.
- Define functions with positional args, keyword args, defaults, `*args`, and `**kwargs`.
- Explain variable scope (local vs. global) and avoid common scoping bugs.
- Use `lambda` for short anonymous functions.
- Handle runtime errors with `try / except / else / finally` and raise your own exceptions.

---

## 2. Concept Reading

### 2.1 The Four Core Data Structures

Python ships with four general-purpose collection types. Picking the right one matters for correctness and performance.

| Type    | Syntax      | Ordered?   | Mutable?                  | Allows duplicates?    | Typical use                                                |
| ------- | ----------- | ---------- | ------------------------- | --------------------- | ---------------------------------------------------------- |
| `list`  | `[1, 2, 3]` | Yes        | Yes                       | Yes                   | Ordered sequence, dynamic size                             |
| `tuple` | `(1, 2, 3)` | Yes        | No                        | Yes                   | Fixed record; dict key; function return of multiple values |
| `dict`  | `{"a": 1}`  | Yes (3.7+) | Yes                       | Keys: No, Values: Yes | Key-based lookup                                           |
| `set`   | `{1, 2, 3}` | No         | Yes, Values are immutable | No                    | Deduplication; membership tests; set math                  |

---
#### 2.1.0 List [ ]

```python
# List — mutable, ordered

fruits = ["apple", "banana", "cherry"]

# add to end
fruits.append("date")       #['apple', 'banana', 'cherry', 'date']

# insert at specific index, all elements shift to right
fruits.insert(1, "avocado")#['apple', 'avocado', 'banana', 'cherry', 'date']

# replace at specific index, previous value is gone
fruits[3] = "Mango"       #['apple', 'avocado', 'banana', 'Mango', 'date']

# remove by value
fruits.remove("banana")   #['apple', 'avocado', 'Mango', 'date']

# delete from last index
fruits.pop()

print(fruits)              # ['apple', 'avocado', 'Mango']
```


List slicing

```python
Address = ["Bengaluru", "Kolkata", "Mumbai", "Delhi", "Bhubaneshwar"]

# start : 1, End : 3
print(Address[1:3]) # ['Kolkata', 'Mumbai']

# start : 0 (default), End : 3
print(Address[:3]) # ['Kolkata', 'Mumbai'] #['Bengaluru', 'Kolkata', 'Mumbai']

# start : 2, End : len(Address)
print(Address[2:]) # ['Mumbai', 'Delhi', 'Bhubaneshwar']

```

Sort a list by ascending and descending order : 

```python
numbers = [5, 0, 4, 3, 2, 1]
address = ["Bengaluru", "Kolkata", "Mumbai", "Delhi"]

# sort() directly changed the original list
numbers.sort()
address.sort()
  
print(numbers) # [0, 1, 2, 3, 4, 5]
print(address) # ['Bengaluru', 'Delhi', 'Kolkata', 'Mumbai']

# ----------------------------------------------------------------

# sort() descending order
numbers.sort(reverse=True)
address.sort(reverse=True)


print(numbers) # [5, 4, 3, 2, 1, 0]
print(address) # ['Mumbai', 'Kolkata', 'Delhi', 'Bengaluru']
```

```python
# reverse the original list
numbers.reverse()
address.reverse()
```

---
#### 2.1.1 Tuple ( )

```python
# Slicing works with tuple
numbers = (4, 3, 1, 2, 0)

# start : 1, End : 3
print(numbers[1:3]) # (3, 1)

# start : 0 (default), End : 3
print(numbers[:3]) # (4, 3, 1)

# start : 2, End : len(numbers)
print(numbers[2:]) # (1, 2, 0)
```

```python
# Tuple — immutable, ordered
point = (3.0, 7.5)              # x, y coordinates
x, y = point                    # unpacking

print(x)                        # 3.0
print(y)                        # 7.5
```


---
#### 2.1.2 Dict (key-value)

```python

# Dict — key-value pairs
person = {
	"name": "Alice",
	"age": 30,
	"isAdult" : True
}

# add/update a new key
person["city"] = "Berlin"

print(person) # {'name': 'Alice', 'age': 30, 'isAdult': True, 'city': 'Berlin'}

# accessig a key-value
# Throws Error if key is not available 
print(person["age"])    # 30
print(person["name"])   # Alice
print(person["Salary"]) # KeyError: 'Salary'
  

# Does not Throws Error if key not found
# If no value is returned, default value is returned

print(person.get("Salary", 10000)) # 10000
print(person.get("age", 0))        # 30



# return all keys
print(person.keys()).   # dict_keys(['name', 'age', 'isAdult', 'city'])


# return all values
print(person.values())  # dict_values(['Alice', 30, True, 'Berlin'])


# return key-value as tuples
print(person.items())   # dict_items([('name', 'Alice'), ('age', 30), ('isAdult', True), ('city', 'Berlin')])

  
# Update this dictionary using another dictionary.
person.update({"age" : 35})

# update() can update multiple keys at once.
person.update({
	"age": 40,
	"interest": "Football"
	})

another_dict = {
	"age": 45,
	"interest": "Chess"
	}

person.update(another_dict)
```

we can also store `list` or `tuple` in `dist` data

```python

person = {
	"name": "Alice",
	"age": 30,
	"isAdult" : True,
	"subjects" : ["Java", "Python", "JavaScript"],
	"topics" : ("dict", "tuple")
}
```

----
#### 2.1.3 Set { } : unique, unordered

```python
#duplicates will be ignored
set_items = {3, "python", 1, "python", "Java", 2, 3}

print(set_items)           # {1, 2, 3, 'python', 'Java'}
```

```python
# add en eliment
set_items.add("Rust")       # {1, 2, 3, 'Rust', 'Java', 'python'}

# remove an element
set_items.remove("Java")    # {1, 2, 3, 'python', 'Rust'}

# deletes and element from any random index
set_items.pop()
set_items.pop()

# Empties the set
set_items.clear()

print(set_items)              # set()
print("python" in set_items)  # True  — O(1) lookup
```

```python
items1 = {2, 3, 1}
items2 = {5, 2, 4, 3}

# Cobines two sets and retured a new unique & orderd set
print(items1.union(items2)) # {1, 2, 3, 4, 5}

# Cobines common values & retured a new unique & orderd set
print(items1.intersection(items2)) # {2, 3}
```

---

**When to use each:**
- Need an ordered, changeable sequence? → `list`
- Need a fixed, hashable collection (e.g., dict key)? → `tuple`
- Need fast key-based lookup? → `dict`
- Need to eliminate duplicates or check membership quickly? → `set`

---

### 2.2 Indexing and Slicing

Python uses zero-based indexing. Using the index number we can access the element of the particular index Negative indices count from the end.


```python
# definig a list
items = ["a", "b", "c", "d", "e"]

# defining a string
text = "Hello, World!"

# accessing list via Indexing
print(items[0])    # "a"
print(items[-1])   # "e"

# accessing string characters via Indexing
print(text[1])     # "e"

```



```python
# definig a list
items = ["a", "b", "c", "d", "e"]

# defining a string
text = "Hello, World!"

# Slicing  [start:stop:step]  — stop is exclusive
print(items[1:4])   # ["b", "c", "d"]
print(items[::-1])  # ["e", "d", "c", "b", "a"]  — reversed
print(items[::2])   # ["a", "c", "e"]             — every other

print(text[0:5])    # "Hello"
print(text[7:])     # "World!"
print(text[:13])    # "World!"
print(text.upper()) # "HELLO, WORLD!"
```


---

### 2.3 Mutability

**Mutable** objects can be changed in place; **immutable** ones cannot.

```python
# List is mutable
a = [1, 2, 3]
b = a           # b points to the SAME list
b.append(4)
print(a)        # [1, 2, 3, 4]  — a changed too!

# Copy to avoid this
c = a.copy()    # or list(a) or a[:]
c.append(5)
print(a)        # [1, 2, 3, 4]  — a unchanged

# Tuple is immutable
t = (1, 2, 3)
# t[0] = 99    # TypeError — cannot assign to tuple item
```

> **Gotcha:** `dict` and `set` are also mutable. Pass them to functions with care — the function can modify the original.

---

### 2.4 Iteration Patterns

**Basic Iteration** : Basic `for` loop, it iterates over each element.

```python
colors = ["red", "green", "blue"]

# We are not accessing the index
for color in colors:
    print(color)      
```

```text
red
green
blue
```

---

**enumerate()** :  It gets index and value together

```python
colors = ["red", "green", "blue"]

# enumerate — get index and value together
for i, color in enumerate(colors):
    print(f"{i}: {color}")
    
    
# ------- without enumerate()-----
# This also did same thing but above loop is recommended
for i in range(len(colors)):
    print(i, colors[i])


```

```terminal
0: red
1: green
2: blue
```

---

**zip()** : It iterate two sequences in lockstep

```python
colors = ["red", "green", "blue"]    
sizes = ["S", "M", "L"]

for color, size in zip(colors, sizes):
    print(f"{color} / {size}")
```

```
red / S
green / M
blue / L
```


```python
ids = [101, 102, 103]
names = ["Alice", "Bob", "Charlie" ]

for id, name in zip(ids, names):
	print(f"{id} : {name}")
```

```
101 : Alice
102 : Bob
103 : Charlie
```

---
**Dictionary Iteration** with **items()**

```python
# dict.items() — key + value pairs

scores = {
	"Alice": 95, 
	"Bob": 82, 
	"Carol": 91
	}

for name, score in scores.items():
    print(f"{name}: {score}")
```

```
Alice: 95
Bob: 82
Carol: 91
```

---

```python
# dict.keys() and dict.values()
print(list(scores.keys()))    # ["Alice", "Bob", "Carol"]
print(list(scores.values()))  # [95, 82, 91]
```

---

### 2.5 Comprehensions

Comprehensions are concise, readable alternatives to `for` loops that build new collections.


#### 2.5.1 **List comprehension — squares of even numbers**

**Syntax pattern :**  Build List

```PYTHon
[
	expression 
	for item in iterable 
	if condition
]

[
	 expression
	 for item in collection
]

```

```python
numbers = [1, 2, 3, 4, 5, 6, 7, 8]

even_squares = [
	n ** 2 
	for n in numbers 
	if n % 2 == 0
	]
	
print(even_squares)   # [4, 16, 36, 64]

```

---
#### 2.5.2 Dict comprehension

```PYTHon
{
	key:value
	for item in dict 
}
```


**print name and their length** 

```python
names = ["Alice", "Bob", "Carol"]

name_lengths = {
	name: len(name)
	for name in names
	}
	
print(name_lengths)   # {"Alice": 5, "Bob": 3, "Carol": 5}
```

---
#### 2.5.3 Set comprehension — unique first letters

```python
{
value
for ...
}
```

```python
words = ["apple", "avocado", "banana", "blueberry", "cherry"]

first_letters = {
	word[0] 
	for word in words
	}
	
print(first_letters)  # {"a", "b", "c"}
```

---

#### 2.5.4 When should you use a list comprehension instead of a `for` loop?

>Use a **list comprehension** when you're creating a new collection with simple transformation or filtering.
>
>Use a **regular `for` loop** when the logic is more complex, involves multiple steps, side effects (like logging or database calls), or readability would suffer.


---

### 2.6 Functions

Functions let you name, reuse, and test a block of logic.

```python
# Basic definition
def greet(name):
    """Return a greeting string for name."""   # docstring
    return f"Hello, {name}!"

print(greet("Alice"))   # Hello, Alice!
```

#### Argument types

##### Positional args — must be passed in order

```python
def add(x, y):
    return x + y

add(3, 4)       # 7
add(y=4, x=3)   # keyword call — order doesn't matter
```


##### Default values — must come after positional args

```python
def power(base, exponent=2):
    return base ** exponent

power(3)        # 9  (uses default exponent=2)
power(3, 3)     # 27
```


##### `*args` — collects extra positional args into a tuple

```python
def total(*numbers):
    return sum(numbers)

print(total(1, 2))             # 3
print(total(1, 2, 3, 4))       # 10
print(total(5, 2, -1, 0, -2))  # 4
```


##### `**kwargs` — collects extra keyword args into a dict

```python
def show_info(**details):
    for key, value in details.items():
        print(f"  {key}: {value}")# name: Alice role: Engineer level: 3

show_info(name="Alice", role="Engineer", level=3)
```

#### Docstrings

Write a docstring (triple-quoted string immediately after `def`) to explain what the function does, its parameters, and what it returns. Tools like `help()` and IDE tooltips display this automatically.

```python
def celsius_to_fahrenheit(celsius):
    """
    Convert a temperature from Celsius to Fahrenheit.

    Args:
        celsius (float): Temperature in degrees Celsius.

    Returns:
        float: Temperature in degrees Fahrenheit.
    """
    return celsius * 9 / 5 + 32
```

---

### 2.7 Variable Scope

A variable's **scope** is the region of code where it is visible.

```python
x = 10          # global scope

def show():
    x = 99      # local variable — does NOT change the global x
    print(x)    # 99

show()
print(x)        # 10 — global x unchanged

# Use 'global' to intentionally modify a global (use sparingly)
counter = 0

def increment():
    global counter
    counter += 1

increment()
print(counter)  # 1
```

> **Best practice:** Avoid `global`. Pass values in as arguments and return results instead. It makes functions easier to test and reason about.

---

### 2.8 Lambda Functions

- `lambda` creates a short, anonymous function in a single expression. 
- There is no `return` keyword inside lambda function . Python automatically returns the result of the expression.
- It is most useful as an argument to higher-order functions like `sorted()`, `map()`, and `filter()`.

**lambda syntax :** 
```python
lambda parameters : expression
```

#### 2.8.0 Normal function vs Lambda function

##### Example 1 - square root of a number 

```python
# normal function
def square(n):
    return n * n
    
print(square(5)) # 25


# ---- lambda function ----
square = lambda n: n ** 2
print(square(5))   # 25
    
```

---
##### Example 2 - addition of two numbers

```python
# normal function
def add(a, b):
    return a + b

print(add(5, 3))      # 8

    
# ---- lambda function ----
add = lambda a, b: a + b
print(add(5, 3)).     # 8
```

---
##### Example  3 - check if a number is even or odd

```python
# normal function
def is_even(n):
return n % 2 == 0

print(is_even(8))
  

# ---- lambda function ----
is_even = lambda n : n%2 == 0
print(is_even(7))
```

---
##### Example  4 - Sort students based on marks

```python
# normal function
students = [
    ("Alice", 90),
    ("Bob", 80),
    ("Charlie", 95)
]

def get_marks(student):
return student[1]


students.sort(key=get_marks)

print(students) # [('John', 75), ('Bob', 80), ('Alice', 90), ('Charlie', 95)]


# ---- lambda function ----

# sort by marks
students.sort(key=lambda student: student[1])


print(students) 
# [('John', 75), ('Bob', 80), ('Alice', 90), ('Charlie', 95)]


# sort by name
students.sort(key=lambda student: student[0])

print(students) 
# [('Alice', 90), ('Bob', 80), ('Charlie', 95), ('John', 75)]
```

---
##### Example - 4

```python
# Common use — sort by a derived key
words = ["banana", "fig", "apple", "cherry"]
words.sort(key = lambda w: len(w))
print(words)   # ['fig', 'apple', 'banana', 'cherry']

# Same thing with a regular function (prefer this for anything non-trivial)
def by_length(w):
    return len(w)

words.sort(key=by_length)
```

---
### 2.8.1 Lambda with map()


```python
numbers = [1,2,3,4]
result = []

for n in numbers:
	result.append(n*n)

print(result)        # [1, 4, 9, 16]
```

```python
numbers = [1,2,3,4]
result = map(
	lambda n: n*n,
	numbers
)
print(list(result))  # [1, 4, 9, 16]
```

---
### 2.8.2 Lambda with filter()

```python
numbers = [1,2,3,4,5,6]

result = filter(
	lambda n: n % 2 == 0,
	numbers
)

print(list(result)) # [2, 4, 6]
```

---
### 2.9 Lambda vs Comprehension

- Python developers usually prefer Comprehension over lambda. 
- A lambda can contain **only one expression**. We cannot write multiple statements inside a lambda. If the logic is more than one expression, use a normal `def`.

**Example 1 - square each number from a list**

```python
# lambda example
numbers = [1, 2, 3, 4, 5, 6]

squares = list(map(lambda n:n*n,numbers))

print(squares) # [1, 4, 9, 16, 25, 36]
```

```python
# prefered comprehensions example
numbers = [1, 2, 3, 4, 5, 6]
squares = [
	n*n 
	for n in numbers
]
print(squares) # [1, 4, 9, 16, 25, 36]
```


**Example 2 - filter even numbers from  a list**

```python
# lambda example
numbers = [1, 2, 3, 4, 5, 6]
even_numbers = list(filter(lambda n:n%2==0,numbers))
print(even_numbers) # [2, 4, 6]
```

```python
# prefered comprehensions example
numbers = [1, 2, 3, 4, 5, 6]
even_numbers = [
	n 
	for n in numbers 
	if n%2==0
]
print(even_numbers) # [2, 4, 6]
```

---

### 2.10 Error Handling

Python signals errors by **raising exceptions**. Use `try / except` to handle them gracefully.

#### Basic `try` / `except`

- Use the `try` block to write **code that may raise an exception**.

- Use `except` to handle the exception. It is similar to `catch` block in Java.


```python
def safe_divide(a, b):
	# Code that may raise an exception
	try:
		result = a / b
		print("valid input")
		print (result)

	# Runs if an exception occurs. 
	except ZeroDivisionError:
		print("Cannot divide by zero.")
	
	# ALWAYS runs — good for cleanup
	finally:
		print("safe_divide finished.")
```

#### `finally`: 

`finally` always guaranteed run — whether an exception occurred or not, and even if the function returns mid-way. 

It is used for  It is typically used for
-   Close a file
-   Close a database connection
-   Release a lock
-   Close a network socket

---
#### The `else` Block

Instead of mixing risky code + non-risky code inside  `try`, Python encourages separating them.

notice in this example, only the line `result = a / b` is a risky code and may raise a `ZeroDivisionError`. other lines of code are not risky. 

So we can separate them in the else block.

``` python
result = a / b        # Code that may raise ZeroDivisionError
print("Valid input")  # Normal processing (not risky)
print(result)         # Normal processing (not risky)
```

```python
def safe_divide(a, b):
    try:
        result = a / b

    except ZeroDivisionError:
        print("Cannot divide by zero.")
        return None

    else:
        # Runs only if no exception occurs.
        print("Valid input")
        print(result)
        return result

    finally:
        # ALWAYS runs — good for cleanup
        print("safe_divide finished.")


print(safe_divide(10, 2))
# Valid input
# 5.0
# safe_divide finished.
# 5.0

print(safe_divide(10, 0))
# Cannot divide by zero.
# safe_divide finished.
# None
```

#### Catching multiple exceptions

```python
data = {"score": "ninety"}

try:
    score = int(data["score"])       # raises ValueError
except KeyError:
    print("Key not found in dict.")
except ValueError as e:
    print(f"Bad value: {e}")
    
```

#### Raising exceptions

```python
def set_age(age):
    if not isinstance(age, int) or age < 0:
        raise ValueError(
	        f"Age must be a non-negative integer, got {age!r}"
	        )
    return age
```

#### Common built-in exceptions to know

| Exception | Triggered when |
|-----------|----------------|
| `KeyError` | Dict key does not exist |
| `ValueError` | Right type, wrong value (e.g., `int("abc")`) |
| `TypeError` | Wrong type (e.g., `"a" + 1`) |
| `IndexError` | List index out of range |
| `AttributeError` | Object does not have the attribute |
| `ZeroDivisionError` | Division by zero |
| `FileNotFoundError` | File path does not exist |

---

## 3. Hands-on Exercise

Exercise files are in `exercises/day-02/`.

**Files:**
- `starter.py` — code with TODO comments for you to complete
- `solution.py` — reference implementation (check only after you have tried)

**What you will build:**

Given a hardcoded list of employee dictionaries (name, dept, salary), you will implement four functions using the concepts from today:

1. `filter_by_dept` — list comprehension to filter by department
2. `avg_salary_by_dept` — a dict comprehension that groups salaries by department and computes the average for each
3. `highest_paid` — `max()` with a `lambda` key
4. `lookup_employee` — iteration with `try / except KeyError` and a default return value

**How to run:**

```bash
cd /path/to/AI_Training
python3 curriculum/python-foundation/exercises/day-02/starter.py
```

Expected output after completing all TODOs matches the output of `solution.py`.

---
## 4. Self-Check Quiz

**Q1. You need a collection of 500 user IDs where you frequently check "is this ID already seen?" and never need to preserve insertion order. Which type is best?**


A `set`. Membership testing (`id in seen`) is O(1) for sets versus O(n) for lists. Sets automatically discard duplicates, which makes them ideal for "have I seen this?" tracking.



**Q2. What does the following slice return? `"abcdefgh"[2:7:2]`**

`"ceg"`. Starting at index 2 (`c`), stopping before index 7 (`h`), stepping by 2: indices 2, 4, 6 → characters `c`, `e`, `g`.



**Q3. What is the output of this code?**

```python
def append_item(value, lst=[]):
    lst.append(value)
    return lst

print(append_item(1))
print(append_item(2))
```

```
[1]
[1, 2]
```

This is the **mutable default argument** trap. The default list `[]` is created once when the function is defined, not on every call. Subsequent calls share the same list object. The safe fix is `def append_item(value, lst=None): if lst is None: lst = []`.




**Q5. A function is called with `func(1, 2, c=3, d=4)`. Write a signature that captures all four arguments.**

```python
def func(*args, **kwargs):
    print(args)    # (1, 2)
    print(kwargs)  # {"c": 3, "d": 4}
```

`*args` collects extra positional arguments into a tuple; `**kwargs` collects extra keyword arguments into a dict.



**Q6. What exception does `scores["Zara"]` raise when `"Zara"` is not a key in `scores`?**

`KeyError`. To avoid it, use `scores.get("Zara")` which returns `None` by default, or `scores.get("Zara", 0)` for a custom default.


---

## 5. Concept Deep-Dive Q&A

**Q1. Python lists and tuples both store ordered sequences. Under the hood, what is the key difference that makes tuple "hashable" and list not?**




CPython stores both as arrays of object pointers. The critical difference is **mutability**: a tuple's contents cannot change after creation, which guarantees that its hash value is stable for its entire lifetime. Python's hashing contract requires that `hash(obj)` never change while `obj` is in use as a dict key or set element. Because a list can be modified at any time, it cannot satisfy this contract — so `list.__hash__` is set to `None` and Python raises `TypeError: unhashable type: 'list'` if you try to use one as a key.



**Q2. How does Python's `for` loop actually work? What protocol does an object need to implement to be iterable?**




When Python encounters `for x in obj`, it calls `iter(obj)`, which invokes `obj.__iter__()` and expects an **iterator** in return. An iterator is any object with a `__next__()` method that returns the next value or raises `StopIteration` when exhausted. Lists, tuples, dicts, sets, strings, and files all implement `__iter__`. You can make your own class iterable by defining `__iter__` and `__next__`. Generator functions (using `yield`) produce iterators automatically without writing those dunder methods.



**Q3. What is the difference between a shallow copy and a deep copy for a list of dicts? When does each matter?**

`list.copy()`, `list(original)`, and `original[:]` all produce a **shallow copy**: a new list object, but each element is still the same object reference. If the elements are mutable (e.g., dicts), modifying an element in the copy also modifies the original.

```python
import copy
original = [{"x": 1}, {"x": 2}]
shallow  = original.copy()
shallow[0]["x"] = 99          # also changes original[0]["x"]

deep = copy.deepcopy(original)
deep[0]["x"] = 42             # original is unaffected
```

Use `copy.deepcopy()` when the collection contains nested mutable objects and you need full independence. It is slower and rarely necessary for flat structures.



**Q4. Explain Python's LEGB scope resolution rule with an example.**

When Python looks up a variable name it searches four scopes in order — **L**ocal → **E**nclosing → **G**lobal → **B**uilt-in:

```python
x = "global"

def outer():
    x = "enclosing"

    def inner():
        # x = "local"  # uncomment to use local scope
        print(x)       # finds "enclosing" (E before G)

    inner()

outer()   # prints "enclosing"
```

- **Local**: variables assigned inside the current function.
- **Enclosing**: variables in any containing (closure) function.
- **Global**: module-level variables.
- **Built-in**: Python's built-in names (`len`, `print`, `range`, etc.).

The `global` keyword forces a name to bind at the global scope; `nonlocal` forces it to bind at the nearest enclosing scope.



**Q5. Why are dict comprehensions generally preferred over building a dict with a loop and repeated `.update()` or `[]` assignment calls?**

Three reasons:

1. **Readability**: the transformation logic is visible in a single expression rather than spread across setup + loop + assignment.
2. **Avoiding repeated attribute lookups**: a manual loop calls `dict.__setitem__` (or `dict.update`) on each iteration; a comprehension avoids that ceremony, though both are O(n) — avoid overstating the performance difference.
3. **Scope isolation**: variables used inside a comprehension do not leak into the surrounding scope (in Python 3), so you avoid accidentally shadowing outer names.

The exception: if the construction logic has side-effects, branches, or is complex enough to be confusing in one line, a plain loop is clearer and should be preferred.



**Q6. What does `*args` actually pass when you call a function? How would you "unpack" an existing list into positional arguments?**


Inside the function `*args` is a plain `tuple` containing the extra positional arguments in the order they were passed. No magic object — just a tuple.

To pass an existing list (or any iterable) as separate positional arguments, use the `*` **unpacking operator** at the call site:

```python
def add(a, b, c):
    return a + b + c

values = [1, 2, 3]
result = add(*values)   # equivalent to add(1, 2, 3)
print(result)           # 6
```

Similarly, `**mapping` at the call site unpacks a dict into keyword arguments.



**Q7. When should you raise a custom exception class instead of using a built-in one like `ValueError`?**

Use custom exceptions when:

- **Callers need to distinguish your errors from other errors of the same built-in type.** If your library raises `ConfigurationError(ValueError)`, callers can `except ConfigurationError` without accidentally catching every `ValueError` from unrelated code.
- **You need to attach structured data to the error** (e.g., `PaymentError(amount=150, currency="USD")` carries context that a plain string message does not.
- **You are building a library or package** where consumers need a stable API to catch errors from your code specifically.

For small scripts and internal utilities, built-in exceptions are usually sufficient and clearer. Start with built-ins; promote to custom exceptions when callers need finer-grained handling.



---

## 6. Key Takeaways

- **Choose your data structure deliberately**: list for ordered mutable sequences, tuple for immutable records, dict for key-based lookup, set for membership and deduplication.
- **Slice syntax** `[start:stop:step]` works on any sequence; `stop` is always exclusive; negative indices count from the end.
- **Mutability matters for copying**: a shallow copy shares nested objects with the original — use `copy.deepcopy()` when you need full independence.
- **Iteration helpers** (`enumerate`, `zip`, `dict.items()`) eliminate manual index tracking and make loops more expressive.
- **Comprehensions** (list, dict, set) are the Pythonic way to transform and filter collections in one readable expression.
- **Functions** should be small, well-named, documented with a docstring, and avoid relying on global state — pass data in, return data out.
- **`*args` / `**kwargs`** let you write flexible functions that accept any number of positional or keyword arguments.
- **LEGB** (Local → Enclosing → Global → Built-in) is Python's name-resolution order; avoid `global` by passing values as arguments.
- **`lambda`** is best for short, single-expression keys passed to `sorted()` or `max()`; use a named `def` for anything more complex.
- **Handle errors where you can do something useful**: catch specific exceptions, provide meaningful messages, and use `finally` for cleanup.
