
>[!question] What is the difference between DROP, DELETE & TRUNCATE

- **DELETE:** The DELETE statement removes specific rows one at a time, based on a condition( using WHERE clause). DELETE Can be Rollback. 
- **TRUNCATE :** Delete all rows at once from table without Deleting any columns. The actual table structure exists in memory. It cannot have a WHERE clause. Cannot be Rollback.
- **DROP:** Deletes the entire table or database completely. Delete all things associated with the tables are dropped as well (relationship, constraints), Table does not exist in Memory. Cannot be Rollback.
---

>[!question] Having vs Where Clause in SQL 
- **WHERE:** WHERE applies to individual rows, it filters rows without grouping. The where clause works on row’s data, not on aggregated data, it cannot be used with aggregate functions.
- **HAVING:** HAVING clause applies to groups. It filters grouped data after the GROUP BY clause has been applied. It is used with aggregates.

---

>[!question] UNION VS JOIN
- **UNION** in SQL is used to combine the result set of two or more SELECT statements. The data combined using the UNION statement is into results into new distinct rows. UNION Merge two table column wise
- **JOIN** in SQL is used to combine data from many tables based on a matched condition between them. The data combined using the JOIN statement results in new columns. Join merge two tables row wise
---
>[!question] Difference between JOIN and UNION in SQL

| **JOIN**                                                                                                     | **UNION**                                                                                   |
| ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------- |
| The SQL JOIN is used when we have to extract data from many tables based on a matched condition between them | The SQL UNION is used when we have to display the results of two or more SELECT statements. |
| The records are combined into new columns.                                                                   | It combines data into new rows                                                              |
| The number of columns selected from each table may not be the same.                                          | The number of columns selected from each table should be the same.                          |
