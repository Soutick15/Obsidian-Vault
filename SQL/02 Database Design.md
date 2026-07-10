---

---

![[Pasted image 20260710171750.png]]




```
02 Database Design.md

1. What is Database Design?

2. Entities

3. Attributes
   - Simple Attribute
   - Composite Attribute
   - Multivalued Attribute
   - Derived Attribute

4. Keys
   - Primary Key
   - Foreign Key
   - Candidate Key
   - Composite Key
   - Alternate Key
   - Super Key

5. Relationships
   - One-to-One (1:1)
   - One-to-Many (1:N)
   - Many-to-Many (M:N)
   - Self Relationship

6. ER Diagram
   - What is an ER Diagram?
   - Components of an ER Diagram
       - Entity
       - Attribute
       - Relationship
       - Cardinality
       - Participation
   - Symbols Used
   - Example ER Diagram

7. Mapping ER Diagram to Tables

8. Best Practices

9. Interview Questions
```


---

## What is an ER Diagram: 

An Entity-Relationship (ER) Diagram is a visual representation of entities, their attributes, and the relationships between them. It is commonly used in database design to map out the structure and relationships in a database system.

### Components of an ER Diagram:

### 1.Entities:

- Entity means real life objects in the database, such as “Students,” “Courses,” or “Employees.” Etc
- Similar types of entities are Denoted by rectangles.
- Two types:

- **Strong Entity:** Can exist independently (e.g., Student).
- **Weak Entity:** Depends on another entity for its existence (e.g., OrderItem).

### 2. Attributes: 

- Represent properties or details about an entity (e.g., Name, ID, Salary pf employee). 
- An entity is described using set of attributes.
- Denoted by ellipses.

#### Types of attributes:

- **Simple Attribute:** Atomic, cannot be divided further (e.g., Age).
- **Composite Attribute:** Can be divided into smaller sub-parts (e.g., Full Name into First Name and Last Name).
- **Derived Attribute:** Can be calculated from other attributes (e.g., Age derived from Date of Birth).
- **Multivalued Attribute:** Can have multiple values (e.g., Phone Numbers).


### 3. Relationships: 

- Represent associations between two or more entities (association between teacher and students).
- Denoted by diamonds.
- A set of similar relationship is called Relationship-Set.

### One-to-One 
This can be defined as the relationship between two tables where each record in one table is associated with the maximum of one record in the other table.
### One-to-Many & Many-to-One 
This is the most commonly used relationship where a record in a table is associated with multiple records in the other table.

### **Many-to-Many**
This is used in cases when multiple instances on both sides are needed for defining a relationship.
### Self-Referencing Relationships
This is used when a table needs to define a relationship with itself.


### 4. Primary Key (PK): 

A unique identifier for an entity (e.g., StudentID for Student entity).
**Key:** An attribute or set of attributes whose values can uniquely identify an entity in a set.

### 5. Foreign Key (FK): 

An attribute in one entity that refers to the primary key of another entity.

#### Domain: A unique set of values permitted for an attribute.

---
SQL syntax is case insensitive but Its a good practice to write sql in CAPITAL.

But table/ columns/ database names are case sensitive.

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

