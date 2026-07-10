# SQL Data Types

SQL data types specify the type of data that a column can hold. They are categorised as follows:

## 1. Numeric Data Types:

- `INT` / `INTEGER`: Whole numbers.
- `SMALLINT` : Smaller range of integers.
- `BIGINT` : Larger range of integers.
- `DECIMAL` / `NUMERIC` : Fixed precision numbers (e.g., DECIMAL(10,2) for 10 digits, 2 after the decimal).
- `FLOAT` / `REAL` : Approximate floating-point numbers.

---
## 2. Character/String Data Types:

- CHAR(n): Fixed-length string (e.g., CHAR(5) always stores 5 characters).
- VARCHAR(n): Variable-length string (e.g., VARCHAR(255) allows up to 255 characters).
- TEXT: Large text data.

---
## 3. Date and Time Data Types:

- DATE: Stores dates (YYYY-MM-DD).
- TIME: Stores time (HH:MM:SS).
- DATETIME: Stores both date and time (YYYY-MM-DD HH:MM:SS).
- TIMESTAMP: Stores date and time with timezone info.

---
## 4. Boolean Data Type: 

BOOLEAN: True/False or 1/0.

---
## 5. Other Data Types: 

BLOB: Binary large objects (e.g., images, audio)., JSON: Stores JSON-formatted data. 

SQL Datatypes: Signed & Unsigned In SQL, numeric data types can be signed or unsigned. 

**Signed**: Allows both negative and positive values. 
- TINYINT (-128 to 127)

**Unsigned**: Allows only positive values (starting from 0).
- TINYINT UNSIGNED (0 to 255)


```sql
CREATE TABLE ExampleTable (
    id TINYINT UNSIGNED, -- Allows values from 0 to 255
    score TINYINT        -- Allows values from -128 to 127
    );
```