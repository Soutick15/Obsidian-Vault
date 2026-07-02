"""
Day 4 Exercise — Classes, Type Hints & Pydantic
=================================================
Complete every TODO below.  Run with:
    python curriculum/python-foundation/exercises/day-04/starter.py

Expected output (exact order):
  --- Part 1: @dataclass ---
  Department(name='Engineering', headcount=12)

  --- Part 2: Pydantic — valid employee ---
  {'name': 'Priya Sharma', 'dept': 'Engineering', 'salary': 80000, 'email': 'priya@example.com'}

  --- Part 3: Pydantic — invalid employee ---
  Caught ValidationError (2 error(s)):
    - salary: Value error, salary must be > 0 [input_value=-500]
    - email: value is not a valid email address [...]

  --- Part 4: Context manager ---
  Computed sum=499999500000  Elapsed: ...s
"""

# ---------------------------------------------------------------------------
# Imports (all provided — do NOT add pip installs here;
# run:  pip install -r curriculum/python-foundation/exercises/requirements.txt)
# ---------------------------------------------------------------------------
import re
import time
from dataclasses import dataclass
from pydantic import BaseModel, field_validator, ValidationError

import logging

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(message)s")
logger = logging.getLogger(__name__)


# ===========================================================================
# PART 1 — @dataclass
# ===========================================================================

# TODO 1: Define a @dataclass called Department with two fields:
#   - name: str
#   - headcount: int
#
# After defining it, create an instance:
#   eng = Department(name="Engineering", headcount=12)
# and print it.  The __repr__ is generated automatically.

# YOUR CODE HERE


# ===========================================================================
# PART 2 — Pydantic BaseModel (valid data)
# ===========================================================================

# TODO 2a: Define a Pydantic v2 BaseModel called Employee with these fields:
#   - name:   str
#   - dept:   str
#   - salary: int
#   - email:  str
#
# TODO 2b: Add a @field_validator for "salary" (decorated with @classmethod)
#   that raises ValueError("salary must be > 0") when salary <= 0.
#
# TODO 2c: Add a @field_validator for "email" (decorated with @classmethod)
#   that uses _EMAIL_RE to check format; raise ValueError("value is not a valid email address")
#   if the pattern does not match.

# YOUR CODE HERE


VALID_DATA = {
    "name": "Priya Sharma",
    "dept": "Engineering",
    "salary": 80_000,
    "email": "priya@example.com",
}

# TODO 2d: Parse VALID_DATA into your Employee model and print model_dump().
#   Hint: Employee(**VALID_DATA)  or  Employee.model_validate(VALID_DATA)

# YOUR CODE HERE


# ===========================================================================
# PART 3 — Pydantic ValidationError (invalid data)
# ===========================================================================

INVALID_DATA = {
    "name": "Bad Actor",
    "dept": "HR",
    "salary": -500,        # violates your validator
    "email": "not-an-email",  # violates EmailStr
}

# TODO 3: Wrap Employee(**INVALID_DATA) in a try/except ValidationError block.
#   On error print:
#       Caught ValidationError (<N> error(s)):
#         - <loc>: <msg>
#   for each error in e.errors().
#   Hint: each error dict has keys "loc" (tuple), "msg" (str).

# YOUR CODE HERE


# ===========================================================================
# PART 4 — Context manager
# ===========================================================================

class Timer:
    """Prints elapsed time when the with-block exits."""

    # TODO 4a: Implement __enter__.
    #   Record the start time (time.perf_counter()) and return self.
    def __enter__(self):
        # YOUR CODE HERE
        pass

    # TODO 4b: Implement __exit__(self, exc_type, exc_val, exc_tb).
    #   Compute elapsed = perf_counter() - self.start and print:
    #       Computed sum=<total>  Elapsed: <elapsed:.4f>s
    #   Return False so exceptions are not suppressed.
    def __exit__(self, exc_type, exc_val, exc_tb):
        # YOUR CODE HERE
        pass


# TODO 4c: Use the Timer context manager to time this computation:
#   total = sum(range(1_000_000))
# Store the result in `total` and print it inside __exit__ as shown above.
# Hint: you can store `total` on the Timer object if needed, OR print inside with.

print("\n--- Part 4: Context manager ---")
# YOUR CODE HERE
