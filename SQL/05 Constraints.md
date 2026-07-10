# Constraints

**Constraints** in SQL specify rules on the data in a table, ensuring accuracy, reliability, and integrity. 

SQL Constraints == Column Attributes)

**Types of SQL Constraints:**

- `NOT NULL` : Ensures a column cannot have NULL values.
- `UNIQUE` : Ensures all values in a column are distinct.
- `PRIMARY KEY` : Uniquely identifies each row in a table.
- `FOREIGN KEY` : Ensures referential integrity by linking to a primary key in another table.
- `CHECK` : Ensures that all values in a column satisfy a specific condition.
- `DEFAULT` : Sets a default value for a column when no value is specified.
---
## NOT NULL : 

Ensures that a column cannot have NULL values.

Syntax (during table creation): column_name datatype NOT NULL;

```sql
CREATE TABLE Students (
	StudentID INT NOT NULL,
	Name VARCHAR(50) NOT NULL
);
```

---

## UNIQUE : 
Ensures all values in a column are distinct or unique.

Syntax: column_name datatype UNIQUE;

```sql
CREATE TABLE Users (
	UserID INT UNIQUE,
	Email VARCHAR(255) UNIQUE
);
```
  

```sql
INSERT INTO Users 
	VALUES (1, "abc@gmail.com"),
		   (1, "abc@gmail.com"); --  Error because duplicate email
```

---
## PRIMARY KEY / COMPOSITE KEY

**Primary key :** 
It is a column or set of columns in a table that uniquely identifies each row. (a unique id). There can only be one primary key in a table, A primary key column cannot contain NULL values. 

```sql
CREATE TABLE Students (id INT PRIMARY KEY, name VARCHAR(50),salary BIGINT );
```


**composite primary key :** 
Primary key can be combination of two columns also called as composite primary key, it’s used when a single column isn’t sufficient to uniquely identify a record.
compexample :


**Combining two columns to act as a unique identifier (composite key).**

```sql
CREATE TABLE EmployeeProjects 
	(EmployeeID INT, ProjectID INT, 
		PRIMARY KEY (EmployeeID, ProjectID)
	);
```

EmployeeID +  ProjectID == primary key

  
**AUTO_INCREMENT PRIMARY KEY** 

```sql
CREATE TABLE Shops ( ShopID INT AUTO_INCREMENT PRIMARY KEY, PRODUCTS VARCHAR(50));
```


| id (Primary Key) | name       | city_id (ForeignKey) | City   |
| ---------------- | ---------- | -------------------- | ------ |
| 101              | Soutick    | 1                    | Pune   |
| 102              | Tanmay Dey | 2                    | Mumbai |
| 103              | Abhishek   | 1                    | Pune   |
| 104              | Sushree    | 3                    | Delhi  |
| 105              | Shovan     | 2                    | Mumbai |


| id (Primary Key) | city_name |
| ---------------- | --------- |
| 1                | Pune      |
| 2                | Mumbai    |
| 3                | Delhi     |

---
### FOREIGN KEY: 

A foreign key is a column or set of columns in a table that refers to the primary key in another table. 

- There can be multiple FKs. 
- Foreign Keys can have duplicate & null values. 
- Foreign key usually creates a kind of link between the two tables. 

syntax :
```sql
FOREIGN KEY (column_name) REFERENCES parent_table (column_name);
```

Example 
```sql
CREATE TABLE Orders ( OrderID INT PRIMARY KEY, CustomerID INT, 
	FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID));
```

**Cascading for foreign Key:** 

- **ON UPDATE CASCADE** : When we create a foreign key using UPDATE CASCADE, The referencing rows are updated in the child table, when the referenced row is updated in the parent table which has a primary key.

- **ON DELETE CASCADE** :It deletes the referencing row in the table when the referenced row is deleted in the parent table which has a primary key.


```sql
CREATE TABLE dept ( 
	dep_ID INT PRIMARY KEY, 
	department_name VARCHAR(50), 
	Id INT, 
	FOREIGN KEY (Id) REFERENCES student(rollno) 
	ON UPDATE CASCADE
	ON DELETE CASCADE

);
```

---

### CHECK
Ensures that values meet a specific condition.

```sql
column_name datatype CHECK (condition);
```

example
```sql
CREATE TABLE Employees (
	EmpID INT PRIMARY KEY,
	Salary DECIMAL(10,2) CHECK (Salary > 0)
);
```
  
---
### DEFAULT
Assigns a default value to a column if no value is provided. if value is not inserted during insertion ,DEFAULT sets the default value of a column the value that is set during the column creation. 

Syntax
```sql
column_name datatype DEFAULT default_value;
```

Example
```sql
CREATE TABLE Products (
	ProductID INT PRIMARY KEY,
	Stock INT DEFAULT 100
	);
```

  ---
  

### INDEX (Optional Constraint): 
Improves query performance by creating an index on one or more columns.

```sql
CREATE INDEX index_name ON table_name(column_name);
```

```sql
CREATE INDEX idx_lastname ON Employees(LastName);
```

---
