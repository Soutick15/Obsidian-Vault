# Functions

SQL functions are broadly categorised into:

1. **Single-Row Functions :** Operate on a single row and return one result per row (e.g., MOD, SQRT, ROUND, LOWER).

2. **Multi-Row (Aggregate) Functions :** Operate on multiple rows and return a single aggregated result (e.g., COUNT, SUM, AVG).

## Single-Row Functions : 

Mathematical Functions
- MOD (Modulus): Returns the remainder of a division.
- SQRT (Square Root): Returns the square root of a number.
- POWER (Exponentiation): Returns a number raised to the power of another.
- ABS (Absolute Value): Returns the absolute (positive) value of a number.
- FLOOR (Floor Value): Rounds a number down to the nearest integer.


```sql
SELECT MOD(10, 3) AS Remainder; -- Output: 1

SELECT SQRT(16) AS SquareRoot; -- Output: 4

SELECT POWER(2, 3) AS Exponentiation; -- Output: 8

SELECT FLOOR(5.8) AS FloorValue; -- Output: 5
```


>[!question] Find employees with salaries rounded off:
```sql
SELECT FirstName, ROUND(Salary, -3) AS RoundedSalary FROM Employees;
```


>[!question] Calculate the total salary of employees grouped by department:
```sql
SELECT Department, SUM(Salary) AS TotalSalary FROM Employees GROUP BY Department;
```


>[!question] Replace all occurrences of ‘Intern’ with ‘Trainee’ in job titles:
```sql
SELECT REPLACE(JobTitle, 'Intern', 'Trainee') AS UpdatedJobTitle FROM Employees;
```
--

>[!question] Query the sum of Northern Latitudes (LAT_N) from STATION having values greater than 38.7880 and less than 137.2345.Truncate your answer to  decimal places.
```mysql
# MySQL
SELECT ROUND(SUM(LAT_N), 4) FROM STATION WHERE LAT_N > 38.7880 AND LAT_N < 137.2345; 
```

>[!question] Query the sum of Northern Latitudes (LAT_N) from STATION having values greater than 38.7880 and less than 137.2345.Truncate your answer to  decimal places.
>
```sql
-- DB2 SQL
SELECT DECIMAL(SUM(LAT_N), 10, 4) FROM STATION WHERE LAT_N > 38.7880 AND LAT_N < 137.2345; 
```


>[!question] We define an employee's total earnings to be their monthly salary * months worked, and the maximum total earnings to be the maximum total earnings for any employee in the Employee table. Write a query to find the maximum total earnings for all employees as well as the total number of employees who have maximum total earnings. Then print these values as 2  space-separated integers.
```mysql
# MySQL
select (salary * months)as earnings, count(*) from employee group by 1 order by earnings desc limit 1; 
```


>[!question] The sum of all values in LAT_N, LONG_W  rounded to a scale of 2 decimal places.
```mysql
# MySQL
SELECT ROUND(SUM(LAT_N), 2), ROUND(SUM(LONG_W), 2) FROM STATION;
```

---

### String Functions : 

- **UPPER:** Converts text to uppercase.
- **LOWER:** Converts text to lowercase.
- **TRIM:** Removes leading and trailing spaces.
- **REPLACE:** Replaces occurrences of a substring with another string.
- **CONCAT:** Combines two or more strings into one.
- **SUBSTRING (or SUBSTR):** Extracts a portion of a string.
- **LENGTH:** Returns the length of a string in characters.

```sql
SELECT UPPER('hello') AS UpperCase; -- Output: HELLO

SELECT LOWER('HELLO') AS LowerCase; -- Output: hello

SELECT TRIM('   hello   ') AS TrimmedText; -- Output: 'hello'

SELECT REPLACE('I love SQL', 'love', 'like') AS ReplacedText; -- Output: I like SQL

SELECT CONCAT('Hello', ' ', 'World') AS CombinedText; -- Output: Hello World

SELECT SUBSTRING('Database', 1, 4) AS Substring; -- Output: Data

SELECT LENGTH('MySQL') AS StringLength; -- Output: 5
```

---
### Date and Time Functions

- **NOW :** Returns the current date and time.
- **CURDATE :** Returns the current date.
- **DATEDIFF :** Calculates the difference between two dates.
- **DATE_FORMAT :** Formats a date in a specified format.
- **CONCAT :** Combines two or more strings into one.
- **SUBSTRING (or SUBSTR) :** Extracts a portion of a string.
- **LENGTH :** Returns the length of a string in characters.

```sql
SELECT NOW() AS CurrentDateTime;

SELECT CURDATE() AS CurrentDate; -- Output: YYYY-MM-DD

SELECT DATEDIFF('2024-12-31', '2024-01-01') AS DateDifference; -- Output: 364

SELECT DATE_FORMAT(NOW(), '%d-%M-%Y') AS FormattedDate; -- Output: 24-Nov-2024

SELECT CONCAT('Hello', ' ', 'World') AS CombinedText; -- Output: Hello World

SELECT SUBSTRING('Database', 1, 4) AS Substring; -- Output: Data

SELECT LENGTH('MySQL') AS StringLength; -- Output: 5

```

---

## SQL Aggregate Functions.

Aggregate functions perform calculations on a set of values and return a single value, often used with the GROUP BY clause. Some Common Aggregate Functions mentioned below.

 - **COUNT():** Counts the number of rows or non-NULL values in a column.
 - **SUM():** Calculates the total sum of numeric values in a column.
 - **AVG():** Computes the average of numeric values in a column.
 - **MIN():** Returns the smallest value in a column.
 - **MAX():** Returns the largest value in a column.
 - **CAST() :** In SQL, CAST is used to convert a value from one data type to another. It is often used to ensure compatibility between data types during calculations or comparisons.

### `COUNT()` : Counts the number of rows or non-NULL values in a column.

```sql
-- Counts the number of non-NULL rollno entries in the student table.
SELECT COUNT(rollno) FROM student;

-- Counts all rows in the Employees table.
SELECT COUNT(*) AS "Total Employees" FROM Employees;

-- Count the distinct departments in the Employees table.
SELECT COUNT(DISTINCT Department) AS "Unique Departments" FROM Employees;
```

---

### `SUM()` : Calculates the total sum of numeric values in a column.

```sql
-- Calculate the total salary of employees earning more than 50,000.
SELECT SUM(Salary) AS "High Salaries Total" FROM Employees WHERE Salary > 50000;

-- Calculate the total of distinct bonuses in the Employees table.
SELECT SUM(DISTINCT Bonus) AS "Total Distinct Bonuses" FROM Employees;

-- Calculate the total of basic salary and bonuses.
SELECT SUM(Salary + Bonus) AS "Total Compensation" FROM Employees;

-- List departments where the total salary exceeds 200,000.
SELECT Department, SUM(Salary) AS "Total Salary" FROM Employees GROUP BY Department HAVING SUM(Salary) > 200000;
```

---
### AVG(): Computes the average of numeric values in a column.

SYNTAX :

```sql
SELECT AVG(column_name) FROM table_name;
```

Example :

```sql
-- Calculate the average salary of employees in the “IT” department.
SELECT AVG(Salary) AS "Average IT Salary" FROM Employees WHERE Department = "IT";

-- Groups employees by department and calculates the average salary for each group.
SELECT Department, AVG(Salary) AS "Average Department Salary" FROM Employees GROUP BY Department;

-- Calculate the average of distinct salaries in the Employees table.
SELECT AVG(DISTINCT Salary) AS "Average Distinct Salary" FROM Employees;

-- Calculate the average of total compensation (salary + bonus).
SELECT AVG(Salary + Bonus) AS "Average Total Compensation" FROM Employees;
```

---
### `MIN()`: Returns the smallest value in a column.

SYNTAX

```sql
SELECT MIN(column_name) FROM table_name;
```


Example :

```sql
-- Find the minimum salary of employees in the “IT” department.
SELECT MIN(Salary) AS "Lowest IT Salary" FROM Employees WHERE Department = "IT";

-- Groups employees by department and shows the lowest salary in each.
SELECT Department, MIN(Salary) AS "Lowest Department Salary" FROM Employees GROUP BY Department;

-- Returns the city name that comes first alphabetically.
SELECT MIN(City) AS "First City" FROM Cities;
```

---
### `MAX()` : Returns the largest value in a column

SYNTAX

```sql
SELECT MAX(column_name) FROM table_name;
```


Example :

```sql
Find the maximum salary of employees in the “Sales” department.
SELECT MAX(Salary) AS "Highest Sales Salary" FROM Employees WHERE Department = "Sales";

-- Groups employees by department and shows the highest salary in each.
SELECT Department, MAX(Salary) AS "Highest Department Salary" FROM Employees GROUP BY Department;

-- Lists employees who have the highest salary in the table.
SELECT FirstName, LastName, Salary FROM Employees WHERE Salary = (SELECT MAX(Salary) FROM Employees);

-- Groups orders by customers and finds the highest order amount for each.
SELECT CustomerID, MAX(OrderAmount) AS "Highest Order" FROM Orders GROUP BY CustomerID;
```

---

### SELECT GROUP_CONCAT(FirstName SEPARATOR ', ') AS AllNames FROM Employees;


```sql
-- Calculate the total salary of employees earning more than 50,000.
SELECT GROUP_CONCAT(FirstName SEPARATOR ', ') AS AllNames FROM Employees;

-- Calculate the total of distinct bonuses in the Employees table.
SELECT SUM(DISTINCT Bonus) AS "Total Distinct Bonuses" FROM Employees;

-- Calculate the total of basic salary and bonuses.
SELECT SUM(Salary + Bonus) AS "Total Compensation" FROM Employees;

-- List departments where the total salary exceeds 200,000.
SELECT Department, SUM(Salary) AS "Total Salary" FROM Employees GROUP BY Department HAVING SUM(Salary) > 200000;
```

---
### `CAST()`: 

In SQL, CAST is used to convert a value from one data type to another. It is often used to ensure compatibility between data types during calculations or comparisons.

SYNTAX
```sql
CAST(expression AS target_data_type)
```

Example

```sql
-- Output: 123 (as an integer)
SELECT CAST('123' AS INT) AS ConvertedValue; 

 -- Output: 123
SELECT CAST(123.45 AS INT) AS RoundedValue;

-- Output: '123' (as a string)
SELECT CAST(123 AS CHAR(10)) AS StringValue; 

-- Output: 2024-11-24 (as a DATE)
SELECT CAST('2024-11-24' AS DATE) AS DateValue;

-- Converts salary to decimal with 2 decimal places
SELECT Name, CAST(Salary AS DECIMAL(10, 2)) AS FormattedSalary FROM Employees;
```


---

### Using Aggregate Functions with GROUP BY: 

Aggregate functions can be combined with the GROUP BY clause to calculate results for groups of data.

```sql
-- Groups employees by their department and calculates the average salary for each department.

SELECT Department, AVG(Salary) AS "Average Salary" FROM Employees GROUP BY Department;
```

```sql
-- Groups students by city and counts the number of students in each city.

SELECT city, count(rollno) FROM student GROUP BY city;
```

```sql
-- Groups students by both city and marks, then counts the number of students in each unique city-marks combination.

SELECT city, marks, count(rollno) FROM student GROUP BY city, marks;
```

```sql
-- Groups students by city and calculates the average marks of students in each city.

SELECT city, AVG (marks) FROM student group by city;
```

```sql
-- Write a query to find average marks in each city in descending order:

SELECT city, AVG (marks) FROM student GROUP BY city ORDER BY AVG(marks) DESC;
```

---
### Using Aggregate Functions with HAVING

The HAVING clause filters groups created by the GROUP BY clause based on aggregate function results. Similar to where which applies condition on rows HAVING is used to apply any condition after grouping.

```sql
SELECT Department, COUNT(*) AS "Total Employees" FROM Employees GROUP BY Department HAVING COUNT(*) > 5;

```

```sql
-- Count number of students in each city where max marks cross 90 
SELECT count(name), city FROM student GROUP BY city HAVING MAX(marks)> 90;
```

---
### Combining Multiple Aggregate Functions: 
We can use multiple aggregate functions in the same query.

```sql
SELECT COUNT(*) AS "Total Employees", AVG(Salary) AS "Average Salary", MAX(Salary) AS "Highest Salary" FROM Employees;
```

---

### SQL Aggregate Functions:General Order

Top to Bottom

```sql
SELECT column(s)

FROM table_name

WHERE condition 

GROUP BY column(s)

HAVING condition

ORDER BY column(s) ASC;
```