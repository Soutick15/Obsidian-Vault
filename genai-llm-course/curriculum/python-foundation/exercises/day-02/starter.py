"""
Day 2 Exercise — Data Structures & Functions
=============================================
You have a hardcoded list of employee dictionaries.
Complete every TODO without adding external libraries.
Run this file to see your output.
"""

# --------------------------------------------------------------------------- #
# Dataset — do NOT modify this block
# --------------------------------------------------------------------------- #
employees = [
    {"name": "Alice",   "dept": "Engineering", "salary": 95000},
    {"name": "Bob",     "dept": "Marketing",   "salary": 72000},
    {"name": "Carol",   "dept": "Engineering", "salary": 108000},
    {"name": "David",   "dept": "HR",          "salary": 65000},
    {"name": "Eve",     "dept": "Marketing",   "salary": 78000},
    {"name": "Frank",   "dept": "Engineering", "salary": 91000},
    {"name": "Grace",   "dept": "HR",          "salary": 70000},
    {"name": "Heidi",   "dept": "Marketing",   "salary": 83000},
]

# --------------------------------------------------------------------------- #
# Task 1 — Filter employees by department
# --------------------------------------------------------------------------- #
def filter_by_dept(emp_list, dept_name):
    """Return a list of employee dicts whose 'dept' matches dept_name."""
    # TODO: use a list comprehension
    pass


# --------------------------------------------------------------------------- #
# Task 2 — Average salary per department
# --------------------------------------------------------------------------- #
def avg_salary_by_dept(emp_list):
    """
    Return a dict mapping each department name to the average salary
    of its employees (rounded to 2 decimal places).

    Example: {"Engineering": 98000.0, "Marketing": 77666.67, "HR": 67500.0}
    """
    # TODO: collect unique departments first, then build the result dict.
    # Hint: a set comprehension gives you unique dept names.
    pass


# --------------------------------------------------------------------------- #
# Task 3 — Find the highest-paid employee
# --------------------------------------------------------------------------- #
def highest_paid(emp_list):
    """Return the employee dict with the maximum salary."""
    # TODO: use the built-in max() with a key argument
    pass


# --------------------------------------------------------------------------- #
# Task 4 — Safe employee lookup by name
# --------------------------------------------------------------------------- #
def lookup_employee(emp_list, name, default=None):
    """
    Search emp_list for an employee whose 'name' matches (case-sensitive).
    Return the employee dict if found, otherwise return default.

    Use try/except to handle the case where a matching employee's dict is
    accessed but 'name' key is somehow missing (KeyError).
    """
    # TODO: iterate emp_list; use try/except KeyError when reading emp["name"]
    pass


# --------------------------------------------------------------------------- #
# Main — prints results; do NOT modify below this line
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    print("=== Task 1: Engineering employees ===")
    eng = filter_by_dept(employees, "Engineering")
    for e in eng:
        print(f"  {e['name']} — ${e['salary']:,}")

    print("\n=== Task 2: Average salary by department ===")
    avgs = avg_salary_by_dept(employees)
    for dept, avg in avgs.items():
        print(f"  {dept}: ${avg:,.2f}")

    print("\n=== Task 3: Highest-paid employee ===")
    top = highest_paid(employees)
    print(f"  {top['name']} ({top['dept']}) — ${top['salary']:,}")

    print("\n=== Task 4: Safe lookup ===")
    found = lookup_employee(employees, "Eve")
    print(f"  Found 'Eve': {found}")
    missing = lookup_employee(employees, "Zara", default={"name": "Unknown", "dept": "N/A", "salary": 0})
    print(f"  Found 'Zara': {missing}")
