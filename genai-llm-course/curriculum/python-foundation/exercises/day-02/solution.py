"""
Day 2 Exercise — Data Structures & Functions  (SOLUTION)
=========================================================
Reference implementation with full explanations in comments.
"""

# --------------------------------------------------------------------------- #
# Dataset
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
    return [emp for emp in emp_list if emp["dept"] == dept_name]


# --------------------------------------------------------------------------- #
# Task 2 — Average salary per department
# --------------------------------------------------------------------------- #
def avg_salary_by_dept(emp_list):
    """
    Return a dict mapping each department name to the average salary
    of its employees (rounded to 2 decimal places).
    """
    # Set comprehension gives us unique dept names
    departments = {emp["dept"] for emp in emp_list}

    # Dict comprehension builds the result in one expression
    return {
        dept: round(
            sum(e["salary"] for e in emp_list if e["dept"] == dept)
            / len([e for e in emp_list if e["dept"] == dept]),
            2
        )
        for dept in departments
    }


# --------------------------------------------------------------------------- #
# Task 3 — Find the highest-paid employee
# --------------------------------------------------------------------------- #
def highest_paid(emp_list):
    """Return the employee dict with the maximum salary."""
    return max(emp_list, key=lambda e: e["salary"])


# --------------------------------------------------------------------------- #
# Task 4 — Safe employee lookup by name
# --------------------------------------------------------------------------- #
def lookup_employee(emp_list, name, default=None):
    """
    Search emp_list for an employee whose 'name' matches (case-sensitive).
    Return the employee dict if found, otherwise return default.
    Uses try/except KeyError when reading emp["name"] for safety.
    """
    for emp in emp_list:
        try:
            if emp["name"] == name:
                return emp
        except KeyError:
            # 'name' key unexpectedly missing — skip this record
            continue
    return default


# --------------------------------------------------------------------------- #
# Main
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
