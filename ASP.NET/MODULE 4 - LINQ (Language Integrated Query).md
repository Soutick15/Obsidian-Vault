
 LINQ : LINQ stands for: Language Integrated Query. It is similar like Java Stream API. 
 
 LINQ in C# is a powerful feature which allows us to process the collections of data efficiently. It is mainly used for Filter Data, Sort Data, Group Data, search data, Transform Data, Aggregate Data.

Imagine we have a huge list —  thousands of records — and we need to perform some operations on it like filtering, sorting, or transforming data. If you use traditional for-loops or iterators, it quickly becomes complex and hard to manage. That’s where LINQ comes in. LINQ allows you to process data in a clean, readable, and functional way, without writing bulky loops.

### Important LINQ Operators and equivalent java stream API methods 

| LINQ                | Java Stream                       |
| ------------------- | --------------------------------- |
| Where()             | filter()                          |
| Select()            | map()                             |
| Count()             | count()                           |
| Any()               | anyMatch()                        |
| All()               | allMatch()                        |
| FirstOrDefault()    | findFirst().orElse(null)          |
| GroupBy()           | Collectors.groupingBy()           |
| OrderBy()           | sorted()                          |
| OrderByDescending() | sorted(Comparator.reverseOrder()) |
| Skip()              | skip()                            |
| Take()              | limit()                           |
| SelectMany()        | flatMap()                         |


Sample Data

```cs
public class Employee
{
    public int Id { get; set; }
    public string Name { get; set; }
    public decimal Salary { get; set; }
    public string Department { get; set; }
}
```


```cs
List<Employee> employees = new List<Employee>();


// Where filters a collection based on a condition and returns matching records.
var result = employees.Where(e => e.Salary > 50000);

// Select Transforms records into another form.
var names = employees.Select(e => e.Name);

// Sort ascending by Name
var result = employees.OrderBy(e => e.Name);

// Sort de-scending by Name
var result = employees.OrderByDescending( e => e.Salary );

// Returns the first matching record if found. If not found, returns null
var employee = employees.FirstOrDefault(e => e.Id == 1 );

// Expects exactly one matching record. Returns null if no record is found. Throws exception if multiple matching records exist.
var employee = employees.SingleOrDefault( e => e.Id == 1 );

// Checks if any object matches the condition or not.
bool exists = employees.Any( e => e.Salary > 100000);

// checks if all objects from the list matches the condition or not.
bool result = employees.All( e => e.Salary > 10000);

//Count records.
int count = employees.Count();

//Count the number where the condition matches
int count = employees.Count( e => e.Salary > 50000 );

// skips the first 10 records. Used mainly for pagination.
employees.Skip(10)

//implement pagination in LINQ using Skip
employees
    .Skip((pageNumber - 1) * pageSize)
    .Take(pageSize);

// returns the next 5 records. Used mainly for pagination.
employees.Take(5)

// Group by Department.
var groups = employees.GroupBy( e => e.Department );

//
var employeesData = employees
        .Where(e => e.Salary > 50000)
        .OrderBy(e => e.Name)
        .Select(e => e.Name);
```


>[!QUESTION] Find the Products where price is more than  ₹5000

```sql
SELECT *
FROM Products
WHERE Price > 5000
ORDER BY Name
```

```cs
var products =
    await _context.Products
        .Where(p => p.Price > 5000)
        .OrderBy(p => p.Name)
        .ToListAsync();
```


>[!QUESTION] Does LINQ execute in memory?

> When used with EF Core, LINQ is translated into SQL and executed in the database.