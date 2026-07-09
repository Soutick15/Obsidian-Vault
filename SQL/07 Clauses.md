# Clauses

## What are SQL CLAUSES?

SQL clause helps us to retrieve a set or bundles of records from the table. Clause specify a condition on the columns or the records of a table.

>[!example]

- WHERE : It Filters rows based on conditions.
- HAVING : It Filters rows based on conditions after grouping.
- ORDER BY : Sorts result set in ascending or descending order.
- GROUP BY : A value into summary rows (e.g., totals, averages). Used with aggregate functions
- LIMIT : Restricts the number of rows returned.
- DISTINCT : Returns unique values, removing duplicates.
- OFFSET


---
## WHERE Clause : Filters rows based on conditions.

Syntax 

```sql
SELECT column1, column2  FROM table_name WHERE condition;
```


```sql
-- Find the names of the customer that are not referred by the customer with referee_id =2 and not null.
select name from Customer where referee_id is null or referee_id!=2;
```

```sql
-- Fetches employees in the IT department earning more than 50,000.
SELECT FirstName, LastName FROM Employees WHERE Salary > 50000 AND Department = 'IT';
```

```sql
-- Fetches employees belonging to either the IT or HR department.
SELECT FirstName, LastName FROM Employees WHERE Department = 'IT' OR Department = 'HR';
```


```sql
-- Fetches employees from IT or HR who earn more than 40,000.
SELECT FirstName, LastName FROM Employees WHERE (Department = 'IT' OR Department = 'HR') AND Salary > 40000;
```

```sql
-- Fetches employees whose LastName is ‘Smith’.
SELECT FirstName, LastName FROM Employees WHERE LastName = 'Smith';
```

```sql
-- Fetches employees earning between 30,000 and 60,000.
SELECT FirstName, Salary FROM Employees WHERE Salary BETWEEN 30000 AND 60000;
```

---
### ORDER BY Clause: Sorts the result set in ascending (ASC) or descending (DESC) order.

```sql
-- Sorts employees by LastName in ascending order (default).
SELECT FirstName, LastName FROM Employees ORDER BY LastName;
```

```sql
-- Explicitly sorts employees by LastName in ascending order.
SELECT FirstName, LastName FROM Employees ORDER BY LastName ASC;
```

```sql
-- Sorts employees by LastName in ascending order. If two employees have the same LastName, it then sorts by FirstName in descending order.

SELECT * FROM Employees ORDER BY LastName ASC, FirstName DESC;
```

```sql
-- Filters employees earning more than 50,000 and sorts them by Salary in descending order.
SELECT FirstName, LastName, Salary FROM Employees WHERE Salary > 50000 ORDER BY Salary DESC;
```

```sql
-- Fetches the top 5 employees with the highest Salary.
SELECT * FROM Employees ORDER BY Salary DESC LIMIT 5;
```

```sql
-- Sorts by Department in ascending order and then by Salary in descending order within each department.
SELECT Department, LastName, Salary FROM Employees ORDER BY Department ASC, Salary DESC;
```

```sql
-- Query the Name of any student in STUDENTS who scored higher than 75 Marks. Order your output by the last three characters of each name. If two or more students both have names ending in the same last three characters (i.e.: Bobby, Robby, etc.), secondary sort them by ascending ID.

SELECT Name FROM STUDENTS WHERE Marks >75 ORDER BY RIGHT(Name, 3), ID ASC;
```

```sql
-- Find the nth highest salary.
SELECT Salary FROM Emp ORDER BY Salary DESC LIMIT (n-1,1);
```

---
### LIMIT Clause (or FETCH in some databases): Restricts the number of rows returned.

syntax 

```sql
SELECT column1, column2 FROM table_name LIMIT number_of_rows;
```

```sql
-- Returns the first 5 rows of the Employees table.
SELECT * FROM Employees LIMIT 5;
```

```sql
-- Skips the first 2 rows and returns the next 5 rows.
SELECT * FROM Employees LIMIT 5 OFFSET 2;
```

```sql
-- retrieves the employee with the highest salary from the Employees table.
SELECT FirstName, Salary FROM Employees ORDER BY Salary DESC LIMIT 1;
```

```sql
-- Fetches 10 rows starting from the 6th row (offset is 5).
SELECT * FROM Employees LIMIT 5, 10;
```

```sql
-- Fetches the last 3 hired employees using a subquery.
SELECT * FROM (SELECT * FROM Employees ORDER BY HireDate DESC LIMIT 3) AS LatestHires;
```

---

### DISTINCT Clause: Returns unique values, removing duplicates.

syntax 
```sql
SELECT DISTINCT column_name  FROM table_name;
```

```sql
-- Returns unique values from the Department column of the Employees table.
SELECT DISTINCT Department FROM Employees;
```

```sql
-- Returns unique combinations of Department and JobTitle.
SELECT DISTINCT Department, JobTitle FROM Employees;
```

```sql
-- Fetches unique last names of employees earning more than 50,000.
SELECT DISTINCT LastName FROM Employees WHERE Salary > 50000;
```

```sql
-- Fetches unique departments and sorts them in ascending order.
SELECT DISTINCT Department FROM Employees ORDER BY Department ASC;
```

```sql
-- Filters employees whose department exists in the list of unique departments.
SELECT * FROM Employees WHERE Department IN (SELECT DISTINCT Department 
FROM Employees);
```

```sql
-- Fetches unique annual salaries calculated as Salary * 12.
SELECT DISTINCT (Salary * 12) AS AnnualSalary FROM Employees;
```

---
### GROUP BY Clause: a value into summary rows (e.g., totals, averages). Often used with aggregate functions like COUNT, SUM, AVG, MIN, MAX.

syntax 

```sql
SELECT column1, aggregate_function(column2) FROM table_name GROUP BY column1;
```

```sql
-- Groups employees by Department and calculates the average salary for each department.

SELECT Department, AVG(Salary) FROM Employees GROUP BY Department;
```

```sql
-- Counts the number of employees in each Department.

SELECT Department, COUNT(*) AS EmployeeCount FROM Employees GROUP BY Department;
```

```sql
-- Calculates the total salary paid in each Department.

SELECT Department, SUM(Salary) AS TotalSalary FROM Employees GROUP BY Department;
```

```sql
-- Groups data by both Department and JobTitle and counts the number of employees for each combination.

SELECT Department, JobTitle, COUNT(*) AS EmployeeCount FROM Employees GROUP BY Department, JobTitle;
```

```sql
-- Groups employees by Department, calculates average salary, and filters groups with an average salary greater than 50,000.

SELECT Department, AVG(Salary) AS AvgSalary FROM Employees GROUP BY Department HAVING AVG(Salary) > 50000;
```

---
### HAVING Clause: Similar to Where i.e. applies some condition on rows. Used when we want to apply any condition after grouping.


```sql
-- Groups students by city and includes only cities where the maximum marks exceed 90.

SELECT city, COUNT(name) AS StudentCount FROM student GROUP BY city 
HAVING MAX(marks) > 90;
```


```sql
-- Groups employees by Department and filters departments with more than 5 employees.

SELECT Department, COUNT(*) AS EmployeeCount FROM Employees GROUP BY Department HAVING COUNT(*) > 5;
```

```sql
-- Groups students by city and includes only cities where the maximum marks exceed 90.
SELECT city, COUNT(name) AS StudentCount FROM student GROUP BY city HAVING MAX(marks) > 90;
```

```sql
-- Filters employees earning more than 30,000 (WHERE), groups by Department, and includes only departments with an average salary greater than 50,000 (HAVING).

SELECT Department, AVG(Salary) AS AvgSalary FROM Employees WHERE Salary > 30000 GROUP BY Department HAVING AVG(Salary) > 50000;
```

```sql
-- Groups employees by Department and includes only departments with employee counts between 5 and 10.

SELECT Department, COUNT(*) AS EmployeeCount FROM Employees GROUP BY Department HAVING EmployeeCount BETWEEN 5 AND 10;
```

```sql
-- Includes departments with an employee count greater than the employee count in the HR department.

SELECT Department, COUNT(*) AS EmployeeCount FROM Employees GROUP BY Department HAVING COUNT(*) > (SELECT COUNT(*) FROM Employees WHERE Department = 'HR');
```

---
### Aliases : Used to rename columns or tables for readability.

```sql
-- Renames FirstName to “Employee Name” and Salary to “Annual Income” in the result set.

SELECT FirstName AS "Employee Name", Salary AS "Annual Income" FROM Employees;
```

```sql
-- Works the same as above but without double quotes (quotes are optional if no spaces or special characters are used).

SELECT FirstName AS EmployeeName, Salary AS AnnualIncome FROM Employees;
```

```sql
-- Shortens the Employees table name to e for easier reference.

SELECT e.FirstName, e.LastName FROM Employees AS e;
```

```sql
-- Uses table alias e for clarity and renames FirstName and Salary for readability.

SELECT e.FirstName AS Name, e.Salary AS Income FROM Employees AS e;
```

```sql
-- Renames Department to “Dept” and the result of AVG(Salary) to “Average Salary”.

SELECT Department AS "Dept", AVG(Salary) AS "Average Salary" FROM Employees GROUP BY Department;
```

```sql
-- Renames columns and assigns an alias DeptSummary to the subquery for better understanding.

SELECT DeptName, TotalSalary FROM ( SELECT Department AS DeptName, SUM(Salary) AS TotalSalary FROM Employees GROUP BY Department ) AS DeptSummary;
```


---

```sql
```

```sql
```

```sql
```

```sql
```

```sql
```

```sql
```

```sql
```

```sql
```

```sql
```

```sql
```

```sql
```

```sql
```

```sql
```

```sql
```

```sql
```

```sql
```

```sql
```

```sql
```

```sql
```

```sql
```

```sql
```

```sql
```

```sql
```

```sql
```

```sql
```

```sql
```