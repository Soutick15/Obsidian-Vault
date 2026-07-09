# Views

A **view** is a virtual table that is based on the result of a SQL query. 

- It does not store data itself but displays data from one or more underlying tables. 
- A view always shows up-to-date data. The database engine recreates the view, every time a user queries it.

**Syntax:**

```sql

-- Creating a View
CREATE VIEW view_name AS SELECT column1, column2, ...
	FROM table_name WHERE condition;

-- Deleting a view
DROP VIEW view_name;
```

**Example:**

```sql
CREATE VIEW EmployeeDetails AS SELECT FirstName, LastName, DeptID FROM Employees WHERE Salary > 50000;
```

Querying a View: We Use a view just like a regular table in a query.

```sql
SELECT * FROM EmployeeDetails;
```

---
## Updating a View:

1.Modify the View’s Query :  Use
- `CREATE OR REPLACE VIEW` or 
- `ALTER VIEW` to update the query.

**Syntax:**

```sql
CREATE OR REPLACE VIEW view_name AS SELECT column1, column2, ...
FROM table_name
WHERE condition;
```


```sql
CREATE OR REPLACE VIEW EmployeeDetails AS SELECT FirstName, LastName, Salary FROM Employees WHERE DeptID = 101;
```

---
### Updating Data Through a View 
 
If the view is updateable, changes to the view propagate to the underlying table.

```sql
UPDATE EmployeeDetails SET Salary = 60000 
WHERE FirstName = 'John';
```


**Note**: Not all views are updateable. Views with GROUP BY, aggregate functions, or DISTINCT are typically not updateable.

---
## Dropping a View

```sql
DROP VIEW view_name;

DROP VIEW EmployeeDetails;
```

---

## Advantages of Views:

1. Simplifies complex queries by hiding complex joins and conditions (encapsulating them)

2. Enhances security by Restricts access to sensitive data by exposing only necessary columns.

3. Improves code reusability and readability.

4. Provides a level of abstraction.

5. Maintenance: Updates to the view’s definition automatically reflect in queries.

## Limitations of Views

1. Performance: Complex views may degrade query performance.

2. Dependency: Dropping an underlying table invalidates the view.

3. Limited Update Capability: Not all views are updateable.


### Example: Complex View

```sql
CREATE VIEW SalesSummary AS 
SELECT Customers.CustomerName, Orders.OrderID, SUM(OrderDetails.Quantity * Products.Price) AS 
TotalAmount FROM Customers
JOIN Orders ON Customers.CustomerID = Orders.CustomerID
JOIN OrderDetails ON Orders.OrderID = OrderDetails.OrderID
JOIN Products ON OrderDetails.ProductID = Products.ProductID
GROUP BY Customers.CustomerName, Orders.OrderID;
```

---
