
# Subqueries & CTE

## Subqueries

A subquery is a query nested inside another query. It is enclosed in parentheses and can be used in various parts of a SQL statement.

>[!example] Types of Subqueries:


 1. **Single-row Subqueries:** Returns a single value (row).

```sql
SELECT FirstName, LastName FROM Employees
	WHERE Salary > (SELECT AVG(Salary)
	FROM Employees);
```

  
2. **Multiple-row Subqueries :** Returns multiple rows and is used with operators like IN, ANY, or ALL.
```sql
SELECT FirstName, LastName FROM Employees 
	WHERE DeptID IN (
	SELECT DeptID FROM Departments WHERE Location = 'Bangalore'
	);
```

3. **Correlated Subqueries:** The subquery refers to the outer query and executes for each row of the outer query.

```sql
SELECT E1.FirstName, E1.Salary FROM Employees E1
	WHERE E1.Salary > (SELECT AVG(E2.Salary) FROM Employees E2 
	WHERE E1.DeptID = E2.DeptID);
```
  

4. **Nested Subqueries:** Subqueries inside subqueries, forming multiple levels of queries.

```sql
SELECT FirstName, LastName FROM Employees
	WHERE DeptID = (
	SELECT DeptID FROM Departments WHERE DeptName = (
	SELECT DeptName FROM Projects WHERE ProjectID = 101
	)
);
```

---

 In SELECT Clause:  Used to calculate or fetch derived values.

```sql
SELECT FirstName, LastName, (SELECT AVG(Salary) FROM Employees) AS "Average Salary" FROM Employees;
```
  ---

In WHERE Clause : Filters rows based on the result of the subquery.
```sql
SELECT FirstName, LastName FROM Employees WHERE Salary > (SELECT AVG(Salary) FROM Employees);
```

---

In FROM Clause (Inline Views): Treats the subquery as a derived table.

```sql
SELECT DeptName, AvgSalary
FROM (SELECT DeptID, AVG(Salary) AS AvgSalary FROM Employees GROUP BY DeptID) AS DeptStats
INNER JOIN Departments ON DeptStats.DeptID = Departments.DeptID;
```

---
In HAVING Clause: Used to filter groups based on a subquery’s result.

```sql
SELECT DeptID, AVG(Salary) AS AvgSalary
	FROM Employees GROUP BY DeptID
HAVING AVG(Salary) > (SELECT AVG(Salary) FROM Employees);
```

  

**Subqueries with Comparison Operators**

• Operators: =, <, >, IN, ANY, ALL.

• Example with ANY:

  ```sql
SELECT FirstName, Salary FROM Employees 
	WHERE Salary > ANY (
		SELECT Salary FROM Employees WHERE DeptID = 101
	);
  ```

**with ALL:**

```sql
SELECT FirstName, Salary FROM Employees
	WHERE Salary > ALL (
		SELECT Salary FROM Employees WHERE DeptID = 101
	);
```
**Key Points**

- Subqueries can return scalar (single value), row, or table results.
- They are often used to simplify complex queries.
- Correlated subqueries are slower as they execute for each row of the outer query.
- Subqueries can be replaced by JOINs in many scenarios for better performance.

---
>[!question] Query the Western Longitude (LONG_W) for the largest Northern Latitude (LAT_N) in **STATION** that is less than 137.2345. Round your answer to  decimal places.

```sql
SELECT ROUND(LONG_W,4) FROM STATION WHERE LAT_N = (
	SELECT MAX(LAT_N) FROM STATION WHERE LAT_N < 137.2345
);
```

---