#### Data vs Information

Data is Raw material/ raw facts.
Information : Processed data is called information. Its a meaningful data.

#### Database 
Database is collection of logically related data in an organised format that can be easily insert, retrieve, update and delete. 

#### DBMS : 
A software application used to manage our Data Base is called DBMS (Database Management System). DBMS provides an efficient and effective way to insert, retrieve, update and delete data. DBMS also provides  safety of the Data.

#### Types of DataBases: 

1. Relational DataBase:  
	Data is stored in Table format. Combination of rows and columns 
	Examples: MySQL, PostgreSQL, Oracle DB, MS SQL Server, SQLite.
	Rows (Tuples, Records) +  Column(field, attributes)

2. Non-Relational DataBase(NoSQL): 
	Data is not stored in tables. 
	Example - MongoDB.

3. HDBMS(Hierarchical DBMS) : Datas are stored in form of tree structure and every Data is interconnected with each other
4. NDBMS(NETWORK DBMS)

>[!question] Why DBMS instead of File system ? Problems if File System

- Data redundancy and inconsistency problem.
- Data isolation.
- Integrity problem.
- Atomicity problem.
- Security problem

#### What are the advantages of DBMS?

- Redundancy is controlled.
- Unauthorised access is restricted.
- Providing multiple user interfaces.
- Enforcing integrity constraints.
- Providing backup and recovery.

#### What is SQL? 

Structured Query Language (SQL) is a command language used to interact with relational databases.

It is used to perform CRUD operations : create, Read, Update, Delete

Purpose:
- Retrieve data.
- Insert, update, and delete records.
- create and manage database objects like tables, views, and indexes.
- Control database access.

#### Database Structure
##### School Database

![[Pasted image 20260709160223.png]]


#### What is a Table

A table is where Data is stored in Combination of rows and columns.
- **Rows:** Tuples, Records
- **Column:** field or attributes

| ROLL_NO | NAME              | ADDRESS      | PHONE      | AGE |
| ------- | ----------------- | ------------ | ---------- | --- |
| 1       | Harsh Nayak       | Bhubaneshwar | 8978384723 | 26  |
| 2       | Soutick Samanta   | Kolkata      | 8478382901 | 25  |
| 3       | Sandeep Mahapatra | Mumbai       | 9152819324 | 23  |
| 4       | Rima Das          | Karnataka    | 7404572742 | 29  |

#### Schema: 

- The overall design of the database is called the database schema. 
- This is a collection of **Tables**, which can be split and grouped according to logic.
- The collection of information stored in a the database at a particular moment is called an instance of the database.