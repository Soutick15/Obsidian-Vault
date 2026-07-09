# Stored Procedures

- A stored procedure is a precompiled set of SQL statements stored in the database. 
- It contains a set of operations that are commonly used, complex business logic, or database management.
- Stored procedures are precompiled, so they execute faster than individual SQL queries.
- Like a function Once created, a stored procedure can be executed multiple times without rewriting the SQL code.

├── CREATE PROCEDURE ├── CALL Procedure ├── Parameters ├── Variables ├── Control Flow ├── Error Handling │ └── Stored Functions ├── What is a Stored Function? ├── CREATE FUNCTION ├── RETURN ├── Calling a Function └── Procedure vs Function


## CREATE PROCEDURE

**Syntax:** 
```sql
CREATE PROCEDURE procedure_name
AS
BEGIN

    -- SQL statements --

END;
```

**Example:** 

```sql
CREATE PROCEDURE GetEmployeeDetails
AS
BEGIN
    SELECT FirstName, LastName, Salary
    FROM Employees
    WHERE Salary > 50000;
END;
```


---

## CALL Procedure

- To execute a stored procedure, you use the EXEC or EXECUTE command.
- EXEC procedure_name; 
- EXEC GetEmployeeDetails;

Stored Procedure with Parameters

Stored procedures can accept **input** and **output** parameters to make them dynamic.

### Input Parameters : 
Used to pass data into the procedure.

```sql
CREATE PROCEDURE GetEmployeeByDepartment (@DeptID INT)
AS
BEGIN
    SELECT FirstName, LastName, Salary
    FROM Employees
    WHERE DepartmentID = @DeptID;

END;

EXEC GetEmployeeByDepartment 101; 
```

### Output Parameters: 
Used to return a value from the procedure.

  
Creating a procedure that returns the total count of employees in a department

```sql
CREATE PROCEDURE GetEmployeeCountByDepartment (
    @DeptID INT,               -- Input parameter
    @EmployeeCount INT OUTPUT  -- Output parameter
    )

AS
BEGIN

    SELECT @EmployeeCount = COUNT(*)
    FROM Employees
    WHERE DepartmentID = @DeptID;

END;

DECLARE @Count INT;  
EXEC GetEmployeeCountByDepartment 101, @Count OUTPUT;  
PRINT @Count;  -- Outputs the number of employees in department 101
```


---
## Modifying a Stored Procedure

To modify an existing stored procedure, you can either drop and recreate it or use the ALTER PROCEDURE statement, depending on the database system.

- **Example (SQL Server):**

```sql
ALTER PROCEDURE GetEmployeeDetails
AS
BEGIN

    SELECT FirstName, LastName, DepartmentID
    FROM Employees
    WHERE DepartmentID = 10;
END;
```
  
---
## Dropping a Stored Procedure
```sql
DROP PROCEDURE procedure_name;
DROP PROCEDURE GetEmployeeDetails;
```


---
## Transaction Control Inside Stored Procedures

Stored procedures can include transaction control statements, such as COMMIT and ROLLBACK, to manage changes within the procedure.

**Example:**

```sql
CREATE PROCEDURE TransferFunds (@FromAccount INT, @ToAccount INT, @Amount DECIMAL)

AS
BEGIN

   BEGIN TRANSACTION;
```

  

```sql
UPDATE Accounts SET Balance = Balance - @Amount 
WHERE AccountID = @FromAccount;

UPDATE Accounts SET Balance = Balance + @Amount 
WHERE AccountID = @ToAccount;
```

```sql
IF @@ERROR <> 0
    BEGIN
        ROLLBACK TRANSACTION;
        PRINT 'Error occurred, transaction rolled back.';
    END
    ELSE
    BEGIN
        COMMIT TRANSACTION;
        PRINT 'Transaction successful.';
    END
END;
```

