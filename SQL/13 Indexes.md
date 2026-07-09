# Indexes

- An index is a database object that improves the speed of data retrieval (SELECT queries) operations by creating a structure based on one or more columns of a table. 

- It allows the database to locate rows more quickly.

- Helps with quick sorting (ORDER BY and GROUP BY).
>[!example] ## Types of Indexes:

### 1. Single-Column Index:

Indexes a single column in a table.

```sql
CREATE INDEX index_name ON table_name(column_name);
CREATE INDEX idx_customer_name ON Customers(CustomerName);
```

---
### 2. Composite Index: 
Indexes two or more columns.

```sql
CREATE INDEX index_name ON table_name(column1, column2);
CREATE INDEX idx_customer_city ON Customers(CustomerName, City);
```

---
### 3. Unique Index: 
Ensures all values in the indexed column(s) are unique.

```sql
CREATE UNIQUE INDEX index_name ON table_name(column_name);
CREATE UNIQUE INDEX idx_unique_email ON Customers(Email);
```

---
### 4. Full-Text Index:
Used for searching text fields in a table. Supported in databases like MySQL.

```sql
CREATE FULLTEXT INDEX idx_description ON Products(Description);
```

---
### 5. Clustered Index:
Determines the physical order of data in the table. Each table can have only one clustered index.

Example (SQL Server): 

```sql
CREATE CLUSTERED INDEX idx_order_id ON Orders(OrderID);
```

---

### 6. Non-Clustered Index: 
Creates a logical ordering of data, separate from the physical table.

Example (SQL Server): 

```sql
CREATE NONCLUSTERED INDEX idx_customer_name ON Customers(CustomerName);
```

---
## View Existing Indexes

```sql
-- MySQL:  
SHOW INDEX FROM table_name;

-- SQL Server: 
SELECT * FROM sys.indexes WHERE object_id = OBJECT_ID(‘table_name');
```

---
### Drop Index

```sql
DROP INDEX index_name ON table_name;
DROP INDEX idx_customer_name ON Customers;
```

---

## Advantages of Indexes

- Faster data retrieval for large datasets.
- Improved performance for queries with WHERE, JOIN, ORDER BY, or GROUP BY clauses.

---
## Disadvantages of Indexes

- Increased storage space.
- Slower INSERT, UPDATE, and DELETE operations due to index maintenance.
- Excessive indexing can degrade performance.

---

## Best Practices for Indexes

- Index columns frequently used in WHERE, JOIN, and ORDER BY.
- Avoid indexing small tables or columns with low selectivity (e.g., columns with many duplicate values).
- Regularly monitor and optimize indexes based on query performance.

---
## **Example:** Optimised Query with Index

```sql
CREATE INDEX idx_lastname ON Employees(LastName);
```

  ```sql
SELECT * FROM Employees WHERE LastName = 'Smith';
  ```
