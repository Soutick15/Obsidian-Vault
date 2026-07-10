# REGULAR EXPRESSION

Regular expressions (RegEx) are patterns used to match character combinations in strings. They are commonly used for string matching, validation, and manipulation. Below is a detailed explanation and examples of regular expressions in SQL and their usage:

**Syntax for Regular Expressions in SQL**

- SQL supports regular expressions using the REGEXP operator in some databases (e.g., MySQL).
- Use REGEXP or RLIKE to apply regular expressions in WHERE clauses.

## The following table lists common regex symbols, their meanings and examples:

|Pattern|Description|Example|Matches|
|---|---|---|---|
|.|Matches any single character (except newline)|h.t|hat, hit, hot|
|^|Matches the start of a string|^A|Apple, Apricot|
|$|Matches the end of a string|ing$|sing, bring|
|\||Acts as logical OR|cat\|dog|cat, dog|
|*|Zero or more of previous character|ab*|a, ab, abb|
|+|One or more of previous character|ab+|ab, abb|
|?|Zero or one of previous character|colou?r|color, colour|
|{n}|Exactly n times|a{3}|aaa|
|{n,}|n or more times|a{2,}|aa, aaa|
|{n,m}|Between n and m times|a{2,4}|aa, aaa, aaaa|
|[abc]|Any one character inside|[aeiou]|a, e, i, o, u|
|[^abc]|Any character not inside|[^aeiou]|any non-vowel|
|[a-z]|Character range|[0-9]|0–9|
|\|Escapes special character|\.|.|
|\b|Word boundary|\bcat\b|cat (not scatter)|
|\B|Non-word boundary|\Bcat|scatter|
|(abc)|Grouping|(ha)+|ha, haha|
|\1|Back-reference|(ab)\1|abab|

## Common Regex Patterns are used to match and find specific text patterns.

| Pattern                                           | Description                                | Example              | Matches               |
| ------------------------------------------------- | ------------------------------------------ | -------------------- | --------------------- |
| ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$ | Validates an email address.                | john.doe@gmail.com   | Valid email addresses |
| ^[0-9]+$                                          | Matches a numeric string only.             | 123456               | 123, 456, 7890        |
| https?://[^ ]+                                    | Matches a URL starting with http or https. | https://example.com/ | URLs                  |
| ^[A-Za-z0-9]+$                                    | Matches alphanumeric strings.              | User123              | abc123, xyz789        |

---

```sql
-- Matches all employees whose first name starts with A.
SELECT * FROM Employees WHERE FirstName REGEXP '^A';
```

```sql
-- Matches products whose names end with Cake.
SELECT * FROM Products WHERE ProductName REGEXP 'Cake$';
```

```sql
-- SELECT * FROM Customers WHERE Email REGEXP 'gmail';
SELECT * FROM Customers WHERE Email REGEXP 'gmail';
```

```sql
-- Matches roll numbers with exactly 5 characters.
SELECT * FROM Students WHERE RollNo REGEXP '^.{5}$';
```

```sql
-- Matches orders where OrderID contains a digit.
SELECT * FROM Orders WHERE OrderID REGEXP '[0-9]';
```

```sql
-- Matches city names that start with A and end with e.
SELECT * FROM Cities WHERE CityName REGEXP '^A.*e$';
```

```sql
-- Matches all employees whose last names do not contain X.
SELECT * FROM Employees WHERE LastName REGEXP '^[^X]*$';
```

```sql
-- Matches employees whose first name is John, Jane, or James.
SELECT * FROM Employees WHERE FirstName REGEXP '^(John|Jane|James)$';
```

```sql
-- MySQL
-- Query the list of CITY names from **STATION** that do not start with vowels, result cannot contain duplicates.
SELECT DISTINCT CITY FROM STATION WHERE CITY REGEXP '^[^aeiou]';
```

```sql
-- Query the list of CITY names from STATION that do not end with vowels. Your result cannot contain duplicates.
SELECT DISTINCT CITY 
	FROM STATION 
		WHERE CITY NOT REGEXP '[aeiouAEIOU]$';

```

```sql

--MySQL
-- Query the list of CITY names from STATION that do not end with vowels. Your result cannot contain duplicates.
SELECT DISTINCT CITY 
	FROM STATION 
		WHERE CITY REGEXP '[^aeiou]$';

```

```sql
-- (DB2)
-- Query the list of CITY names from STATION that do not end with vowels. Your result cannot contain duplicates.
SELECT DISTINCT CITY FROM STATION 
	WHERE RIGHT(CITY, 1) 
		NOT IN (
		'a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U'
		);

```

```sql
--MySQL
-- Query the list of CITY names from STATION that either do not start with vowels or do not end with vowels. Your result cannot contain duplicates.

SELECT DISTINCT CITY FROM STATION 
	WHERE NOT (CITY REGEXP '^[AEIOUaeiou].*[AEIOUaeiou]$');

```


```sql
--MySQL
-- Query the list of CITY names from STATION that either do not start with vowels and do not end with vowels. Your result cannot contain duplicates.
SELECT DISTINCT CITY 
	FROM STATION 
		WHERE CITY REGEXP '^[^AEIOUaeiou].*[^AEIOUaeiou]$';
```


```sql
-- Validates email addresses.
SELECT * FROM Users 
	WHERE Email 
	REGEXP '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$';
```

```sql
-- Matches phone numbers with 10-15 digits, optionally starting with +.
SELECT * FROM Contacts 
	WHERE Phone REGEXP '^\+?[0-9]{10,15}$';
```

```sql
-- Matches employee names containing any vowels.
SELECT * FROM Employees 
	WHERE FirstName REGEXP '[aeiouAEIOU]';
```