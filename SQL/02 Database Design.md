# Database related Queries:


```mysql
# To create a database named db_name;
CREATE DATABASE db_name;

#Creates the database only if it doesn’t already exist.
CREATE DATABASE IF NOT EXISTS Employee;

# Selects the database db_name for subsequent operations.
USE Employee;

# To delete a database named db_name;
DROP DATABASE db_name;

# Deletes the database only if it exists, avoiding errors.
DROP DATABASE IF EXISTS db_name;

# Lists all databases available on the server.
SHOW DATABASES;

# Lists all tables in the currently selected database.
SHOW TABLES;

```



```sql

CREATE TABLE IF NOT EXISTS  emp_info(id INT PRIMARY KEY, name VARCHAR(50),salary BIGINT );
```
SQL syntax is case insensitive but Its a good practice to write sql in CAPITAL.
But table/ columns/ database names are case sensitive.


## SQL Data Types and Table Basics

SQL data types specify the type of data that a column can hold. They are categorised as follows:

**1. Numeric Data Types:**

- INT/INTEGER: Whole numbers.
- SMALLINT: Smaller range of integers.
- BIGINT: Larger range of integers.
- DECIMAL/NUMERIC: Fixed precision numbers (e.g., DECIMAL(10,2) for 10 digits, 2 after the decimal).
- FLOAT/REAL: Approximate floating-point numbers.

**2. Character/String Data Types:**

- CHAR(n): Fixed-length string (e.g., CHAR(5) always stores 5 characters).
- VARCHAR(n): Variable-length string (e.g., VARCHAR(255) allows up to 255 characters).
- TEXT: Large text data.

**3. Date and Time Data Types:**

- DATE: Stores dates (YYYY-MM-DD).
- TIME: Stores time (HH:MM:SS).
- DATETIME: Stores both date and time (YYYY-MM-DD HH:MM:SS).
- TIMESTAMP: Stores date and time with timezone info.

**4. Boolean Data Type:** BOOLEAN: True/False or 1/0.

**5. Other Data Types:** BLOB: Binary large objects (e.g., images, audio)., JSON: Stores JSON-formatted data. 

- **SQL Datatypes:** Signed & Unsigned In SQL, numeric data types can be **signed** or **unsigned**. **Signed**: Allows both negative and positive values. **Unsigned**: Allows only positive values (starting from 0).
- TINYINT UNSIGNED (0 to 255)
- TINYINT (-128 to 127)

  

```mysql

CREATE TABLE ExampleTable (
    id TINYINT UNSIGNED, # Allows values from 0 to 255
    score TINYINT        # Allows values from -128 to 127
   );
```



- Creating Tables : Tables are the fundamental storage objects in a database.

```mysql
CREATE TABLE table_name (
	column1 datatype constraints,
    column2 datatype constraints,
    ...
);
```


```mysql
USE db_name; 
```


```mysql
CREATE TABLE Employees (

    EmpID INT PRIMARY KEY,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50),
    HireDate DATE,
    Salary DECIMAL(10,2)
);
```

| EmpID | FirstName | LastName | HireDate | Salary |
| ----- | --------- | -------- | -------- | ------ |
|       |           |          |          |        |
|       |           |          |          |        |

- `SELECT`: The `SELECT` statement is used to retrieve data from one or more tables in a database.

```mysql
SELECT col1, col2 FROM table_name;     # retrieve only col1, col2
SELECT * FROM table_name;              # Select & View ALL columns:

```


```mysql
SELECT FirstName, LastName FROM Employees;
```

| FirstName | LastName |
| --------- | -------- |
| Soutick   | Samanta  |
| Chandan   | Das      |


```mysql
SELECT * FROM table_name;
```

| EmpID | FirstName | LastName | HireDate   | Salary |
| ----- | --------- | -------- | ---------- | ------ |
| 1     | Soutick   | Samanta  | 04/05/2019 | 45000  |
| 2     | Chandan   | Das      | 12/02/2018 | 55000  |

