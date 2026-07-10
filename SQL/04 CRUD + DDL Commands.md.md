

>[!Example] Types of SQL Commands

## DDL (Data Definition Language): 

- To make Schema related changes/ design changes of the database/ table: 
- DROP, CREATE, ALTER, TRUNCATE, RENAME, COMMENT, USE. (DR-CAT)

## DQL (Data Query Language) :

- SELECT

## DML (Data Manipulation Language): 
- To work on Values or instance of database.
- SELECT, DELETE, INSERT, UPDATE.(DISU)

## DCL (Data Control Language):
- GRANT(to give permission), REVOKE(to take permission).

## TCL (Transaction Control Language): 
- COMMIT, ROLLBACK, SAVEPOINT, SET TRANSACTION.

---

## UPDATE (DML)

Update (to update existing rows): The UPDATE statement is used to modify existing records in a table. You can update one or multiple columns in one or more rows based on a condition.

syntax
```sql
UPDATE table_name SET col1 = val1, col2 = val2 WHERE condition;
```

```sql
-- To disable safe mode:
SAFE SQL_SAFE_UPDATES = 0;
```

```sql
-- To enable safe mode
SAFE SQL_SAFE_UPDATES = 1;
```

```sql
-- Updates the salary to 60000 for the employee with EmpID = 101.

UPDATE Employees SET Salary = 60000 WHERE EmpID = 101;
```

```sql
-- Changes the LastName to “Sharma” and Salary to 75000 for the employee with EmpID = 102.

UPDATE Employees SET LastName = 'Sharma', Salary = 75000 WHERE EmpID = 102;
```

```sql
-- Updates the HireDate to 2023-01-01 for all rows in the Employees table.

UPDATE Employees SET HireDate = '2023-01-01';
```

```sql
-- Updates the salary of the employee with EmpID = 103 to the average salary of the HR department.

UPDATE Employees SET Salary = (SELECT AVG(Salary) FROM Employees WHERE Department = 'HR') WHERE EmpID = 103;
```

---
## RENAME (DDL)

The RENAME statement is used to change the name of a table or column for better readability or structure. The syntax and functionality may vary slightly depending on the database system (MySQL, PostgreSQL, SQL Server, etc.)..

syntax :
```sql
RENAME TABLE old_table_name TO new_table_name;
```

Rename the table Employees to Staff.
```mysql
-- MySQL
RENAME TABLE Employees TO Staff;
```

Some databases allow you to rename multiple tables in one statement.
```mysql
-- MySQL
RENAME TABLE Orders TO CustomerOrders, Payments TO Transactions;
```

Renaming a column can be achieved using the ALTER TABLE statement as RENAME COLUMN is supported in some databases like MySQL 8.0+.
```sql
--SQL
ALTER TABLE table_name RENAME COLUMN old_column_name TO new_column_name;
```

Renaming a column FullName to EmployeeName in the Staff table:
```sql
-- SQL
ALTER TABLE Staff RENAME COLUMN FullName TO EmployeeName;
```

---
## DELETE

The `DELETE` statement is used to remove one or more rows from a table based on a condition.

SYNTAX
```sql
DELETE FROM table_name WHERE condition;
```

```sql
-- Removes the row where StudentID is 101.

DELETE FROM students WHERE StudentID = 101;
```

```sql
-- Deletes all rows from the products table. However, the table structure remains intact.

DELETE FROM products;
```

```sql
-- Removes rows where the Department is HR and Salary is less than 40000.

DELETE FROM Employees WHERE Department = 'HR' AND Salary < 40000;
```

```sql
-- Deletes rows where the Salary is below the average salary of all employees.

DELETE FROM Employees WHERE Salary < (SELECT AVG(Salary) FROM Employees);
```
---

## TRUNCATE

The TRUNCATE command is used to delete Removes all rows from a table. The table remains without any data after truncation. Unlike DELETE, TRUNCATE is usually non-transactional and cannot be rolled back in many databases. Resets auto-increment counters for columns like AUTO_INCREMENT (if applicable). You cannot specify a condition (WHERE clause) with TRUNCATE.

SYNTAX :
```sql
TRUNCATE TABLE table_name;
```

Resetting Auto-Increment Counter: 
**Scenario:** If the table has an auto-increment column, TRUNCATE resets the counter.

```sql
CREATE TABLE employees ( id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(50), salary INT);

INSERT INTO employees (name, salary) VALUES ('John', 50000), ('Alice', 60000);

-- Truncate the table
TRUNCATE TABLE employees;

-- Insert new rows
INSERT INTO employees (name, salary) VALUES ('Bob', 70000);
```

---

- Modifying Tables: The ALTER TABLE statement is used to modify the structure of an existing table. You can add, drop, rename, change, or modify columns and constraints.

Add a Column : 
```sql
ALTER TABLE table_name ADD column_name datatype;
```

Modify a Column :
```sql
ALTER TABLE table_name MODIFY column_name new_datatype;
```

Delete a Column 
```sql
ALTER TABLE table_name DROP COLUMN column_name;

```

Dropping Tables:To delete a table and its data:
```sql
DROP TABLE table_name; 
```


Adds a new column DateOfBirth of type DATE to the Employees table.

```sql
ALTER TABLE Employees ADD DateOfBirth DATE;
```


Filters employees whose department exists in the list of unique departments.
```sql
INSERT INTO emp_info 
	VALUES (4, "Raj Bose", 25000), 
		   (5, "Sushree", 15000);
```

---

**Modifying Tables:** To make changes to an existing table:

**1. Add a Column:** 
```sql
ALTER TABLE table_name ADD column_name datatype;
```

**2. Modify a Column:** 
```sql
ALTER TABLE table_name MODIFY column_name new_datatype;
```

**3. Delete a Column:**

```sql
ALTER TABLE table_name DROP COLUMN column_name;
```

- **Dropping Tables**  To delete a table and its data:
```sql
DROP TABLE table_name;
```


----
## Do this exercise, and interact with the DB

```sql

 -- create database "college"
CREATE DATABASE company; 

 -- delete database "college"
DROP DATABASE company;

DROP DATABASE IF EXISTS company;

 -- create database "college"
CREATE DATABASE IF NOT EXISTS company; 

-- Lists all databases available on the server.
SHOW DATABASES;

 --  use college DB for subsequent operations.
USE company;

CREATE TABLE IF NOT EXISTS Employee (
	id INT PRIMARY KEY,
	name VARCHAR(50),
	salary BIGINT
	);
	
```
	
**Syntax** 
```sql
INSERT INTO table_name (colname1, colname2)
	VALUES 
		(col1_v1, col2_v1),
		(col1_v2, col2_v2);
```


```sql

INSERT INTO Employee (id, name, salary) 
	VALUES 
		(4, "Soutick Samanta", 25000),
		(5, "Tanmay Dey", 15000),
		(6, "Abhishek Atta", 18000);


INSERT INTO Employee 
	VALUES 
		(4, "Shovan Bera", 25000), 
		(5, "Sushree", 15000);


-- Lists all tables in selected database.
SHOW TABLES;
```

```sql
-- Select & View ALL columns:
SELECT * FROM Employee; 
```


| id  | name            | Salary |
| --- | --------------- | ------ |
| 4   | Soutick Samanta | 25000  |
| 5   | Tanmay Dey      | 15000  |
| 6   | Abhishek Atta   | 18000  |
| 4   | Shovan Bera     | 25000  |
| 5   | Sushree         | 15000  |

---

**1. Add a new constraint:** (needs to verify)
```sql
ALTER TABLE Employee ADD CONSTRAINT age INT (age);
```

---
**2. Drop a constraint:**

```sql
ALTER TABLE table_name DROP CONSTRAINT constraint_name;

ALTER TABLE Employees DROP COLUMN Department;
```
