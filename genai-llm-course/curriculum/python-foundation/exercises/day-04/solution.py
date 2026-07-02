"""
Day 4 Exercise — Classes, Type Hints & Pydantic  (SOLUTION)
=============================================================
Run with:
    python curriculum/python-foundation/exercises/day-04/solution.py

Requires:
    pip install -r curriculum/python-foundation/exercises/requirements.txt
"""

import re
import time
from dataclasses import dataclass
from pydantic import BaseModel, field_validator, ValidationError

import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(message)s")
logger = logging.getLogger(__name__)


# ===========================================================================
# PART 1 — @dataclass
# ===========================================================================

@dataclass
class Department:
    name: str
    headcount: int


print("--- Part 1: @dataclass ---")
eng = Department(name="Engineering", headcount=12)
print(eng)
print()


# ===========================================================================
# PART 2 — Pydantic BaseModel (valid data)
# ===========================================================================

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


VALID_DATA = {
    "name": "Priya Sharma",
    "dept": "Engineering",
    "salary": 80_000,
    "email": "priya@example.com",
}

print("--- Part 2: Pydantic — valid employee ---")
emp = Employee.model_validate(VALID_DATA)
print(emp.model_dump())
print()


# ===========================================================================
# PART 3 — Pydantic ValidationError (invalid data)
# ===========================================================================

INVALID_DATA = {
    "name": "Bad Actor",
    "dept": "HR",
    "salary": -500,
    "email": "not-an-email",
}

print("--- Part 3: Pydantic — invalid employee ---")
try:
    Employee.model_validate(INVALID_DATA)
except ValidationError as e:
    errors = e.errors()
    print(f"Caught ValidationError ({len(errors)} error(s)):")
    for err in errors:
        loc = ".".join(str(l) for l in err["loc"])
        msg = err["msg"]
        print(f"  - {loc}: {msg}")
print()


# ===========================================================================
# PART 4 — Context manager
# ===========================================================================

class Timer:
    """Records start time in __enter__ and prints elapsed time in __exit__.

    The caller does not need to set anything on the Timer object — it is
    entirely self-contained.
    """

    def __enter__(self) -> "Timer":
        self.elapsed: float = 0.0
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.elapsed = time.perf_counter() - self._start
        print(f"Elapsed: {self.elapsed:.4f}s")
        return False  # do not suppress exceptions


print("--- Part 4: Context manager ---")
with Timer() as t:
    total = sum(range(1_000_000))
print(f"  sum result: {total}")

logger.info("Day 4 exercise complete.")
