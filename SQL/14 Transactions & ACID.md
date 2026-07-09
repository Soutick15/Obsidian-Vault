# Transactions & ACID

TCL commands in SQL manage transactions within a database. 

A transaction is a group of SQL operations treated as a single unit, which we performed within a DBMS, that ensures all operations (a series of operations like database queries) are either completed successfully as a whole (COMMIT) or in case of failure or none are applied. (ROLLBACK) maintaining the consistency and integrity of the database.

>[!example] ## Key Properties of Transactions (ACID)

**1.Atomicity**: Ensures that a transaction is treated as a single unit of work.

**2.Consistency:** Ensures that the database remains in a valid state before and after the transaction. (one consistent state to another).

**3.Isolation:** Ensures that transactions do not interfere with each other.

**4.Durability:** Once a transaction is committed, the changes are permanent even after a system failure.

#### DATA INTEGRITY: 
Data integrity refers to the overall accuracy, completeness, and reliability of data.
Type:
1. DOMAIN INTEGRITY - restricting the format, type, and volume of data recorded in a database 
2. ENTITY INTEGRITY - The purpose is to ensure that data is not recorded multiple times
3. REFERENTIAL INTEGRITY - remove duplicate data records.
4. User defined INTEGRITY - fulfil their specific requirements.

---
### START TRANSACTION or BEGIN TRANSACTION

The START TRANSACTION or BEGIN TRANSACTION command begins a new transaction in a database. Once a transaction starts, it groups multiple SQL operations into a single unit of work that can be committed or rolled back together.


```sql
BEGIN TRANSACTION; --SQL
```

```mysql
START TRANSACTION; # MySQL
```

---
### COMMIT 

Permanently saves all changes made during the transaction. 

```sql
BEGIN TRANSACTION;

INSERT INTO Employees (EmpID, Name, Salary) VALUES (1, 'John', 50000);
UPDATE Employees SET Salary = 55000 WHERE EmpID = 1;

COMMIT;
```
Both the INSERT and UPDATE changes are saved permanently.

---

### ROLLBACK 

Undoes all changes made during the transaction, reverting the database to its previous state.

```sql
BEGIN TRANSACTION;

INSERT INTO Employees (EmpID, Name, Salary) VALUES (2, 'Alice', 60000);
DELETE FROM Employees WHERE EmpID = 1;

ROLLBACK;
```
No changes are applied. The INSERT and DELETE are undone.

---
### SAVEPOINT

The SAVEPOINT statement creates a named point within a transaction. You can rollback to this point without affecting the preceding part of the transaction.

**Syntax** 
```sql
SAVEPOINT savepoint_name;
```

**Example**

```sql
BEGIN TRANSACTION;

INSERT INTO employees (id, name, salary) VALUES (1, 'John', 50000);

	SAVEPOINT sp1;     -- Savepoint created here

INSERT INTO employees (id, name, salary) VALUES (2, 'Alice', 60000);	
	
	ROLLBACK TO sp1;   -- Rollback to savepoint sp1
	
	COMMIT;            -- Commit changes
```

- Row with ID 1 is inserted. 
- Row with ID 2 is **not inserted** because of the rollback.

---

We can remove a savepoint using 

**syntax**
```sql
RELEASE SAVEPOINT savepoint_name;
```

After releasing, it can no longer be used.

```sql
BEGIN TRANSACTION;

INSERT INTO employees (id, name, salary) VALUES (1, 'John', 50000);

SAVEPOINT sp1;   -- Release the savepoint

RELEASE SAVEPOINT sp1;

ROLLBACK TO sp1; -- Error: sp1 no longer exists.

COMMIT;
```

---

**ROLLBACK TO SAVEPOINT**: 

used to undo all changes made in a transaction after a specific savepoint, without affecting the changes made before that savepoint.

**syntax**
```sql
ROLLBACK TO SAVEPOINT savepoint_name;
```

**Example**
```sql
INSERT INTO Employees (EmpID, Name, Salary) VALUES (1, 'John', 50000);

-- Set a savepoint after the INSERT
SAVEPOINT AfterInsert; 

UPDATE Employees SET Salary = 55000 WHERE EmpID = 1;

 -- Set another savepoint after the UPDATE
SAVEPOINT AfterUpdate;

-- Unintentional delete
DELETE FROM Employees WHERE EmpID = 1; 

-- Reverts the DELETE operation
ROLLBACK TO SAVEPOINT AfterUpdate; 

-- Commit changes
COMMIT;
```

• The DELETE operation is undone.
• The changes made by the INSERT and UPDATE remain.

---

### SET AUTOCOMMIT: 

The SET AUTOCOMMIT command is used to enable or disable the automatic commitment of transactions in a database.

 "0" : Disables autocommit. 
 "1" : Enables autocommit.
**Syntax**
```sql
SET AUTOCOMMIT = {0 | 1};

-- Enable AUTOCOMMIT: Any subsequent SQL statement is committed automatically.
SET AUTOCOMMIT = 1;

-- Disable AUTOCOMMIT: Transactions are now controlled manually.
SET AUTOCOMMIT = 0; 
```

**Example** 
```sql
SET AUTOCOMMIT = 0; -- Disable

INSERT INTO Orders (OrderID, ProductName, Quantity, Price) VALUES (101, 'Laptop', 2, 80000);

UPDATE Orders SET Quantity = 3 WHERE OrderID = 101;

-- Commit the changes
	COMMIT;

-- Disable AUTOCOMMIT and perform more operations
	SET AUTOCOMMIT = 0; 

INSERT INTO Orders (OrderID, ProductName, Quantity, Price) VALUES (102, 'Tablet', 5, 30000);

-- Rollback the changes for the second order

	ROLLBACK;
```

**Order 101**: Inserted and updated because it was committed.
**Order 102**: Not saved because the transaction was rolled back.

---

```sql
-- Start transaction
START TRANSACTION;

-- Deduct $500 from John Doe
UPDATE Accounts SET Balance = Balance - 500 WHERE AccountID = 1;

-- Create a savepoint
SAVEPOINT BeforeTransfer;

-- Add $500 to Jane Smith
UPDATE Accounts SET Balance = Balance + 500 WHERE AccountID = 2;

-- Rollback to the savepoint due to an error
ROLLBACK TO SAVEPOINT BeforeTransfer;

-- Commit the remaining changes
COMMIT;

START TRANSACTION;

UPDATE Accounts SET Balance = Balance - 1000 WHERE AccountID = 1;

UPDATE Accounts SET Balance = Balance + 1000 WHERE AccountID = 2;

-- Error detected, cancel the entire transaction
ROLLBACK;
```