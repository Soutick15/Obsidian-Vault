
## Set Operations

Set operations combine the results of two or more SELECT queries. The queries involved must have The same number of columns. Compatible data types in corresponding columns.

>[!example] Types of Set Operations: 

1. UNION
2. UNION ALL 
3. INTERSECT
4. EXCEPT (or MINUS)

| **Employees_2024** |           |          |            |
| ------------------ | --------- | -------- | ---------- |
| EmpId              | FirstName | LastName | Department |
| 1                  | John      | Doe      | IT         |
| 2                  | Bob       | Brown    | HR         |
| 3                  | Maria     | Johnson  | IT         |

| **Employees_2023** |           |          |            |
| ------------------ | --------- | -------- | ---------- |
| EmpId              | FirstName | LastName | Department |
| 1                  | John      | Doe      | IT         |
| 2                  | Alice     | Smith    | HR         |
| 3                  | Maria     | Johnson  | Finance    |

---
### UNION  
Combines the results of two queries, removing duplicate rows by default.

![[Pasted image 20260710001736.png|114]]


**syntax**
```sql
SELECT column1 FROM table1  
	UNION
SELECT column1 FROM table2;
```

Example 
```sql
SELECT FirstName, Department FROM Employees WHERE Department = 'HR' 
	UNION
SELECT FirstName, Department FROM Employees WHERE Department = 'IT';
```

Example 
```sql
SELECT FirstName FROM Employees_2023 
	UNION
SELECT FirstName FROM Employees_2024;
```

>[!success] output

|               |
| ------------- |
| **FirstName** |
| John          |
| Alice         |
| Maria         |
| Bob           |
Duplicate FirstName values (like "John" and "Maria") appear only once.

---
### UNION ALL: 

Combines the results of two queries, including duplicate rows.
![[Pasted image 20260710001956.png|158]]

```sql
SELECT FirstName FROM Employees_2023 
	UNION ALL 
SELECT FirstName FROM Employees_2024;
```

>[!success] output

|   |
|---|
|FirstName|
|John|
|Alice|
|Maria|
|John|
|Bob|
|Maria|
Duplicate entries (e.g., "John" and "Maria") are retained in the result set.

---
### INTERSECT

Returns only the rows that are present in both queries.
**Note**: Not supported in some databases like MySQL (use JOIN as an alternative).

![[Pasted image 20260710003828.png|192]]
**Syntax:** 

```sql
SELECT column_names FROM table1
	INTERSECT
SELECT column_names FROM table2;
```

Example
```sql
SELECT FirstName FROM Employees_2023
	INTERSECT
SELECT FirstName FROM Employees_2024;
```

>[!success] output

|               |
| ------------- |
| **FirstName** |
| John          |
|Maria|

---

### EXCEPT (or MINUS): 

Returns rows from the first query that are not present in the second query.

**Note**: EXCEPT is supported in PostgreSQL, SQL Server, etc. In Oracle, the equivalent keyword is MINUS.

![[Pasted image 20260710003953.png|223]]

**Syntax:** 

```sql
SELECT column_names FROM table1
	EXCEPT
SELECT column_names FROM table2;
```

Example
```sql
SELECT FirstName FROM Employees_2023
	EXCEPT
SELECT FirstName FROM Employees_2024;
```

>[!success] output

|               |
| ------------- |
| **FirstName** |
| Alice         |

---

##### Example with ORDER BY

To control the final output, you can use ORDER BY after the set operation.

```sql
SELECT City FROM Customers
	UNION
SELECT City FROM Suppliers
ORDER BY City ASC;
```