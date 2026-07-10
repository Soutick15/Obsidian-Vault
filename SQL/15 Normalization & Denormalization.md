# Normalization & Denormalization

When there is same set of data repeated each and every time, it results in duplication of data, either in row or column.

now row level duplicity can be removed by using primary key for unique values. For column level duplicity we use Normalization.

## Normalization:  

Normalization is the process of organising data in a database effectively to 
- Reduce Redundancy to Avoid duplicate data in the database.
- Improve data consistency and accuracy.
- Enhance Query Performance
- Avoids anomalies (problems on specific scenario).

It  involves dividing a database into two or more tables.

Anomalies we can avoid with Normalization :

- **data insertion anomaly:** it occurs when it is difficult to insert data into the database due to the absence of other required data. example, we want to add a new department, but there is no employee in the department yet. 

- **deletion anomaly:**  it occurs when deleting data removes other valuable data. Example if you delete all records in the table, you will lose the track of department, their manager and salaries.

- **Updation anomaly :**  it occurs when changes to data require multiple updates

---

### Forms of Normalization:

#### 1.First Normal Form (1NF):

First step in the normalization process. 

- All columns contain atomic (indivisible) values.
- Each column contains only one value per row (no multi-valued attributes).
- Each column has a unique name and Each row is unique.
- The order of data does not matter.

#### 2. Second Normal Form (2NF)
Meets all 1NF rules.  It has no Partial Dependency (i.e., no non-key attribute should depend on part of a composite key).

#### 3. Third Normal Form (3NF)
Meets all 2NF rules. There is no transitive dependency (non-prime attribute depends on another non-prime attribute).	

#### 4. Boyce-Codd Normal Form (BCNF)
A stricter version of 3NF, ensuring every determinant is a candidate key.

---
## Denormalization

Denormalization is the process of: 
- Introducing redundancy into a database by combining tables or adding precomputed data.
- It improve query performance by reducing the number of joins at the cost of increased storage space and potential update anomalies. 
- It is the opposite of normalization, where normalization eliminates redundancy to ensure data integrity.
- It simplify complex queries for reporting or analytics

### Why is Denormalization Needed?

Although normalization helps reduce redundancy and anomalies, it can lead to:
- Complex queries requiring multiple joins.
- Slower read performance due to excessive joins.
- Increased CPU and memory usage for large datasets.

---

