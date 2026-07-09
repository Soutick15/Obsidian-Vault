# SQL Join

- Joins are used to retrieve data from multiple tables based on a related common column between them. 
- Joins allow us to query data across multiple tables effectively.
- 
>[!example] Types of Joins:

![[Pasted image 20260709221324.png]]


---
## INNER JOIN: 

The INNER JOIN keyword selects records that have matching values in both tables. Rows without matching values are excluded.

syntax :
```sql
SELECT columns FROM table1 
	INNER JOIN table2
ON table1.column_name = table2.column_name;
```

|            | **Customers** |             |
| ---------- | ------------- | ----------- |
| CustomerID | name          | City        |
| 1          | Alice         | New York    |
| 2          | Bob           | Los Angeles |
| 3          | Charlie       | Chicago     |
| 4          | Diana         | New York    |
![[Pasted image 20260709221551.png|209]]

|         | **Orders** |             |
| ------- | ---------- | ----------- |
| OrderID | CustomerID | OrderAmount |
| 101     | 1          | 500         |
| 102     | 2          | 300         |
| 103     | 4          | 200         |
| 104     | 5          | 400         |

### Inner Join Example with Query

>[!question] Query 1: Retrieve customers who have placed orders.

```sql

SELECT Customers.CustomerID, Customers.Name, Orders.OrderAmount
	FROM Customers
	INNER JOIN Orders
ON Customers.CustomerID = Orders.CustomerID;
```

>[!success] Output :

| CustomerID | name         | OrderAmount |
| ---------- | ------------ | ----------- |
| 1          | Alice        | 500         |
| 2          | Bob          | 300         |
| 4          | Diana        | 200         |

---

>[!question] Query 2: Find cities of customers who placed orders of more than 300.

```sql
SELECT Customers.Name, Customers.City, Orders.OrderAmount
	FROM Customers
	INNER JOIN Orders
	ON Customers.CustomerID = Orders.CustomerID
	WHERE Orders.OrderAmount > 300;
```

>[!success] Output :

| name  | City     | OrderAmount |
| ----- | -------- | ----------- |
| Alice | New York | 500         |

---

>[!question] Retrieve orders where customers and orders exist in both tables.

```sql
SELECT Orders.OrderID, Customers.Name
	FROM Orders
	INNER JOIN Customers
	ON Orders.CustomerID = Customers.CustomerID;
```

>[!success] Output :

| OrderID | name    |
| ------- | ------- |
| 101     | Alice   |
| 102     | Bob     |
| 103     | Charlie |

---

## LEFT JOIN (or LEFT OUTER JOIN) 

![[Pasted image 20260709222719.png|266]]


Returns all records from the left table and matching records from the right table. If no match is found, NULL is returned for the right table.

syntax :
```sql
SELECT columns FROM table1
	LEFT JOIN table2
	ON table1.column_name = table2.column_name;
```

### LEFT Join Example with Query

>[!question] Retrieve all customers, whether or not they have placed an order.

```sql
SELECT Customers.CustomerID, Customers.Name, Orders.OrderAmount
	FROM Customers
	LEFT JOIN Orders
	ON Customers.CustomerID = Orders.CustomerID;
```

>[!success] Output :

| CustomerID | name    | OrderAmount |
| ---------- | ------- | ----------- |
| 1          | Alice   | 500         |
| 2          | Bob     | 300         |
| 3          | Charlie | NULL        |
| 4          | Diana   | 200         |

---
>[!question] Find customers from New York, including those who haven’t placed orders.

```sql

SELECT Customers.Name, Customers.City, Orders.OrderAmount
	FROM Customers
	LEFT JOIN Orders
	ON Customers.CustomerID = Orders.CustomerID
	WHERE Customers.City = 'New York';
```
>[!success] Output :

| name  | City     | OrderAmount |
| ----- | -------- | ----------- |
| Alice | New York | 500         |
| Diana | New York | 200         |

---
>[!question] Display all customers, showing “No Orders” for those without orders.

```sql
SELECT Customers.Name, 
	COALESCE(Orders.OrderAmount, 'No Orders') AS OrderAmount
	FROM Customers
	LEFT JOIN Orders
	ON Customers.CustomerID = Orders.CustomerID;
```

>[!success] Output :


| name    | OrderAmount |
| ------- | ----------- |
| Alice   | 500         |
| Bob     | 300         |
| Charlie | No Orders   |
| Diana   | 200         |

---

## RIGHT JOIN (or RIGHT OUTER JOIN)

Returns all records from the right table and matching records from the left table. If no match is found, NULL is returned for the left table.

![[Pasted image 20260709222853.png|189]]

Syntax : 

```sql
SELECT columns FROM table1
	RIGHT JOIN table2
	ON table1.column_name = table2.column_name;
```


>[!question] Query 1: Retrieve all orders, including those that don’t have a matching customer.
>

```sql
SELECT Orders.OrderID, Orders.OrderAmount, Customers.Name 
	FROM Customers 
	RIGHT JOIN Orders
	ON Customers.CustomerID = Orders.CustomerID;
```

>[!success] Output :

| OrderID | OrderAmount | name  |
| ------- | ----------- | ----- |
| 101     | 500         | Alice |
| 102     | 300         | Bob   |
| 103     | 200         | Diana |
| 104     | 400         | NULL  |

---
>[!question] Query 2: Find all orders of more than 300, including unmatched orders.

```sql
SELECT Orders.OrderID, Orders.OrderAmount, Customers.Name
	FROM Customers
	RIGHT JOIN Orders
	ON Customers.CustomerID = Orders.CustomerID
	WHERE Orders.OrderAmount > 300;
```

>[!success] Output :

| OrderID | OrderAmount | Name  |
| ------- | ----------- | ----- |
| 101     | 500         | Alice |
| 104     | 400         | NULL  |

---

>[!question] Query 3: Show all orders with customer details or “Unknown Customer” if unmatched.

```sql
SELECT Orders.OrderID, Orders.OrderAmount, COALESCE(Customers.Name, 'Unknown Customer') AS CustomerName
	FROM Customers
	RIGHT JOIN Orders
	ON Customers.CustomerID = Orders.CustomerID;
```

>[!success] Output :

| OrderID | OrderAmount | CustomerName     |
| ------- | ----------- | ---------------- |
| 101     | 500         | Alice            |
| 102     | 300         | Bob              |
| 103     | 200         | Diana            |
| 104     | 400         | Unknown Customer |

---

## FULL JOIN (or FULL OUTER JOIN)

- The FULL OUTER JOIN keyword returns all records when there is a match in either table. If there is no match, NULL values are returned for columns from the table without a match.


![[Pasted image 20260709223520.png|180]]
 
- MySQL does not support the FULL OUTER JOIN keyword directly. However, you can achieve the same result using a combination of LEFT JOIN, RIGHT JOIN, and UNION. Here’s how to properly implement it:

**Syntax in SQL:** 

```sql
SELECT column_name(s)
	FROM table1
	FULL OUTER JOIN table2
	ON table1.column_name = table2.column_name;
```

**Syntax in MySQL:** 

```mysql
LEFT JOIN
	UNION
RIGHT JOIN
```

```mysql

SELECT * FROM student as a LEFT JOIN course as b ON a.id = b.id
	UNION
SELECT * FROM student as a RIGHT JOIN course as b ON a.id = b.id
```

>[!question] Query 1: Retrieve all customers and all orders, whether matched or not.

```sql
SELECT Customers.CustomerID, Customers.Name, Orders.OrderID, Orders.OrderAmount FROM Customers
	FULL OUTER JOIN Orders
	
	ON Customers.CustomerID = Orders.CustomerID;
```



>[!success] Output :

| CustomerID | name    | OrderID | OrderAmount |
| ---------- | ------- | ------- | ----------- |
| 1          | Alice   | 101     | 500         |
| 2          | Bob     | 102     | 300         |
| 3          | Charlie | NULL    | NULL        |
| 4          | Diana   | 103     | 200         |
| NULL       | NULL    | 104     | 400         |

---

### CROSS JOIN

A CROSS JOIN combines each row from the first table with every row in the second table. It produces a Cartesian product, meaning the number of rows in the result set is the product of the number of rows in the two tables.

**Syntax:** 

```sql
SELECT columnsFROM table1
	CROSS JOIN table2;
```

|           | Products    |
| --------- | ----------- |
| ProductID | ProductName |
| 1         | Laptop      |
| 2         | Phone       |

|         | Colors    |
| ------- | --------- |
| ColorID | ColorName |
| 1       | Black     |
| 2       | White     |

>[!question] Query 1: Combine each product with every color.

```sql
SELECT Products.ProductName, Colors.ColorName
	FROM Products
CROSS JOIN Colors;
```

>[!success] Output :

| ProductName | ColorName |
| ----------- | --------- |
| Laptop      | Black     |
| Laptop      | White     |
| Phone       | Black     |
| Phone       | White     |

---

>[!question] Query 2: Combine products with colors to create unique product variations.

```sql
SELECT CONCAT(Products.ProductName, ' - ', Colors.ColorName) AS ProductVariation FROM Products
	CROSS JOIN Colors;
```

>[!success] Output :

|               |
| ------------- |
| **Hierarchy** |
| Laptop-Black  |
| Laptop-White  |
| Phone-Black   |
| Phone-White   |

---



>[!question] Query 3: Find all possible pairs of employees within the same table (self cross join).

```sql
SELECT E1.Name AS Employee1, E2.Name AS Employee2 FROM Employees E1
	CROSS JOIN Employees E2;
```

>[!success] Output :

| **Employee1** | **Employee2** |
| ------------- | ------------- |
| Alice         | Alice         |
| Alice         | Bob           |
| Alice         | Charlie       |
| Bob           | Alice         |
| Bob           | Bob           |
| …             | …             |

---

## SELF JOIN: 

A SELF JOIN is a join in which a table is joined with itself. It is often used when you want to compare rows within the same table or create hierarchical relationships within the table.

```sql
SELECT A.column_name, B.column_name FROM table_name A
	JOIN table_name B
ON A.common_column = B.common_column;
```

|                | Employees |               |
| -------------- | --------- | ------------- |
| **CustomerID** | **Name**  | **ManagerID** |
| 1              | Alice     | NULL          |
| 2              | Bob       | 1             |
| 3              | Charlie   | 1             |
| 4              | Diana     | 2             |
| 5              | Edward    | 3             |


>[!question] Query 1: List each employee with their manager’s name.

```sql
SELECT E1.Name AS Employee, E2.Name AS Manager FROM Employees E1
	LEFT JOIN Employees E2
ON E1.ManagerID = E2.EmployeeID;
```

>[!success] Output :

| Employee | Manager |
| -------- | ------- |
| Alice    | NULL    |
| Bob      | Alice   |
| Charlie  | Alice   |
| Diana    | Bob     |
| Edward   | Charlie |

---
>[!question] Query 2: Find employees who report to the same manager.

```sql
SELECT E1.Name AS Employee1, E2.Name AS Employee2, E3.Name AS Manager
	FROM Employees E1 
	JOIN Employees E2 ON E1.ManagerID = E2.ManagerID 
	JOIN Employees E3 ON E1.ManagerID = E3.EmployeeID
	WHERE E1.EmployeeID < E2.EmployeeID;
```

>[!success] Output :

| Employee1 | Employee2 | Manager |
| --------- | --------- | ------- |
| Bob       | Charlie   | Alice   |

---


>[!question] Query 3: Display the hierarchy of employees in the organization.

```sql
SELECT CONCAT(E2.Name, ' -> ', E1.Name) AS Hierarchy FROM Employees E1
	LEFT JOIN Employees E2
	ON E1.ManagerID = E2.EmployeeID;
```

>[!success] Output :

|                 |
| --------------- |
| **Hierarchy**   |
| NULL->Alice     |
| Alice->Bob      |
| Alice ->Charlie |
| Bob->Diana      |
| Charlie->Edward |

---
## Using Joins with Aggregate Functions

Joins can be combined with aggregate functions like COUNT, etc., for summarised results.

```sql
SELECT Departments.DeptName, COUNT(Employees.EmpID) AS "Total Employees" FROM Departments 
LEFT JOIN Employees ON Departments.DeptID = Employees.DeptID
GROUP BY Departments.DeptName;
```