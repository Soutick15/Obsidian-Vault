
# Operators:

## Comparison 
`=`, `!=`, `<`, `>`, `<=`, `>=`.



### Arithmetic Operators
`+`(addition) , `-`(subtraction), `*`(multiplication), /(division), %(modulus)

- Pattern Matching : LIKE, NOT LIKE.Null Check: IS NULL, IS NOT NULL.
- Bitwise Operators : & (Bitwise AND), | (Bitwise OR)


## Logical operators :  `AND`, `OR`, `NOT`, `IN`, `BETWEEN`, `ALL`, `LIKE`, `ANY`

### AND (to check for both conditions to be true):

```mysql
SELECT * FROM student WHERE marks > 90 AND city = "Mumbai";
# Fetches all rows where marks are greater than 90 and the city is "Mumbai".
```

```mysql
SELECT * FROM Orders WHERE OrderDate > '2023-01-01' AND ShipCity = "Delhi";
# Returns all orders where OrderDate is after January 1, 2023, and the ShipCity is "Delhi".
```

---
### OR (to check for one of the conditions to be true)

```mysql
SELECT * FROM student WHERE Mathematics > 85 OR Science > 90;
# Fetch all students scoring above 85 in Mathematics or above 90 in Science.
```

```mysql
SELECT * FROM Properties WHERE Area > 1500 OR City = "Delhi";
# List properties with area greater than 1500 sq.ft. or located in “Delhi.”
```

---

### Between (selects for a given range)

```mysql
SELECT * FROM student WHERE marks BETWEEN 80 AND 90;
# Fetch details of students scoring between 80 and 90 marks.
```

```mysql
SELECT * FROM Library WHERE IssueDate BETWEEN '2023-01-01' AND '2023-12-31';
# Retrieve books issued between “2023-01-01” and “2023-12-31.”
```

-----

### In (matches any value in the list) 

- `IN` operator does not work with pattern matching (e.g., `a%`) in SQL. 
- The `IN` operator expects an exact match within a list of discrete values

```mysql
SELECT * FROM student WHERE city IN ('Delhi', 'Mumbai');
# Fetch student details where the city is either “Delhi” or “Mumbai.”
```

```mysql
SELECT * FROM student WHERE rollno IN (101, 102, 105);
# Get details of students with roll numbers 101, 102, or 105.
```

```mysql
SELECT * FROM Orders WHERE OrderDate IN ('2024-01-01', '2024-05-01', '2024-10-01');
# Fetch orders placed on specific dates.
```

```mysql
SELECT CourseID FROM Courses WHERE ProgramID IN (SELECT ProgramID FROM Programs WHERE ProgramType = 'Engineering');
# Fetch all courses taken by students enrolled in specific programs.
```

```mysql
SELECT * FROM Orders WHERE ProductName IN ('%Laptop%', '%Phone%', '%Tablet%');
# Retrieve orders where ProductName includes specific terms.
```

```mysql
SELECT * FROM Products WHERE Category = 'Electronics' AND Brand IN ('Samsung', 'Apple', 'Sony');
# Retrieve products where the category is “Electronics” and brand is among a list of brands.
```

---
### NOT (to negate the given condition)

```mysql
# Retrieve customers who are not from “India” or “USA.”
SELECT * FROM Customers WHERE Country NOT IN ('India', 'USA');
```

```mysql
# Fetch students whose names do not start with “A.”
SELECT * FROM Students WHERE Name NOT LIKE 'A%';
```

```mysql
# Find orders that are not delivered and not shipped by “DHL.”
SELECT * FROM Orders WHERE NOT (Status = 'Delivered' AND ShippingCompany = 'DHL');
```

```mysql
# Retrieve employees whose salaries are not between 40,000 and 60,000.
SELECT * FROM Employees WHERE Salary NOT BETWEEN 40000 AND 60000;
```

```mysql
# Fetch students whose middle names are not NULL.
SELECT * FROM Students WHERE MiddleName IS NOT NULL;
```

```mysql
# Fetch products that are not in the “Electronics” category.
SELECT * FROM Products WHERE NOT Category = 'Electronics';
```

```mysql
# Retrieve employees who do not have a dependent record in the Dependents table.
SELECT * FROM Employees e WHERE NOT EXISTS (SELECT 1 FROM Dependents d WHERE e.EmployeeID = d.EmployeeID);
```

```mysql
# Fetch orders not placed by customers with IDs 101, 102, or 103.
SELECT * FROM Orders WHERE CustomerID NOT IN (101, 102, 103);
```

```mysql
# Fetch students who are not from “Delhi” and do not have marks above 80.
SELECT * FROM Students WHERE NOT (City = 'Delhi' AND Marks > 80);
```

```mysql

# Query the list of CITY names from STATION that either do not start with vowels or do not end with vowels. Your result cannot contain duplicates.

SELECT DISTINCT CITY FROM STATION 
WHERE NOT 
(CITY LIKE 'A%' OR CITY LIKE 'E%' OR CITY LIKE 'I%' OR CITY LIKE 'O%' OR CITY LIKE 'U%') 
OR NOT 
(CITY LIKE '%A' OR CITY LIKE '%E' OR CITY LIKE '%I' OR CITY LIKE '%O' OR CITY LIKE '%U'); -- mySQL
```

```mysql

SELECT DISTINCT CITY FROM STATION
WHERE 
	CITY NOT LIKE 'A%' AND CITY NOT LIKE 'E%' AND CITY NOT LIKE 'I%' AND 
	CITY NOT LIKE 'O%' AND CITY NOT LIKE 'U%' AND CITY NOT LIKE '%A' AND 
	CITY NOT LIKE '%E' AND CITY NOT LIKE '%I' AND CITY NOT LIKE '%O' AND 
	CITY NOT LIKE '%U';

```

---
### LIKE: 
- It is used in SQL to search for a specified pattern in a column.
- `%` : Represents zero or more characters. `" "` : Represents a single character.

```mysql
# Fetch all employees whose names start with “A.”
SELECT * FROM Employees WHERE FirstName LIKE 'A%';
```

```mysql
# Find all products with “Pro” in their names.
SELECT * FROM Products WHERE ProductName LIKE '%Pro%';
```

```mysql
# Retrieve city names with exactly 5 characters.
SELECT * FROM Cities WHERE CityName LIKE '_____';  -- 5 underscores for 5 characters
```

```mysql
# Fetch employees whose names start with “S” and end with “a.”
SELECT * FROM Employees WHERE FirstName LIKE 'S%a';
```

```mysql
# Retrieve students whose names start with “A” or end with “n.”
SELECT * FROM Students WHERE Name LIKE 'A%' OR Name LIKE '%n';
```

```mysql
# Find all customers whose names do not start with “J.”
SELECT * FROM Customers WHERE FirstName NOT LIKE 'J%';
```


```mysql
# Retrieve employees with email addresses ending in “[gmail.com](http://gmail.com).”
SELECT * FROM Employees WHERE Email LIKE '%@[gmail.com](http://gmail.com)';

```

```mysql
# Dynamic Search Using Parameters, Fetch books whose titles match a user-provided pattern.
SELECT * FROM Books WHERE Title LIKE ?;  -- Replace `?` with a user input, e.g., '%Harry%'
```

```mysql
# Retrieve employees whose department names contain “Sales.”
SELECT * FROM Employees WHERE DepartmentID IN (SELECT DepartmentID FROM Departments WHERE DepartmentName LIKE '%Sales%');

```

---
### `IS NULL` and `IS NOT NULL` Operators in SQL

What are `NULL` values in SQL?
- `NULL` represents a missing or unknown value. 
- It is different from zero or an empty string. NULL values indicate that the data is not available or applicable.

- `IS NULL` : To check if a column has a NULL value.

```mysql
SELECT column_name FROM table_name WHERE column_name IS NULL;
```


- `IS NOT NULL` : To check if a column has a non-NULL value.

```mysql
SELECT column_name FROM table_name WHERE column_name IS NOT NULL;
```

```mysql
# The query retrieves rows where Marks is NULL.
SELECT * FROM Students WHERE Marks IS NULL;
```

```mysql
# The query retrieves rows where Marks has a non-NULL value.
SELECT * FROM Students WHERE Marks IS NOT NULL;
```

```mysql
# Find students who scored less than 80 but whose marks are not missing
SELECT * FROM Students WHERE Marks < 80 AND Marks IS NOT NULL;
```

```mysql
# Count students whose marks are NULL.
SELECT COUNT(*) AS MissingMarks FROM Students WHERE Marks IS NULL;
```

```mysql
# Replace NULL marks with a default value (e.g., 0):
UPDATE Students SET Marks = 0 WHERE Marks IS NULL;
```
---
