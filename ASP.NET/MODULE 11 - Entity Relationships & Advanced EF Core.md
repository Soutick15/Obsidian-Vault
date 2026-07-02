>[!Question] Types of Relationships 

Mainly we have three types of Relationships

1. One-to-One
2. One-to-Many
3. Many-to-One
4. Many-to-Many

>[!NOTE] One-to-Many

Example : One Category can have multiple products. Like Electronics category can have multiple products like : Laptop, Mobile, Headphone etc

```CS
public class Category
{
    public int Id { get; set; }
    public string Name { get; set; }
    public ICollection<Product> Products{ get; set;} = new List<Product>();
}
```

``` cs
public class Product
{
    public int Id { get; set; }
    public string Name { get; set; }
    public int CategoryId { get; set; }
    
    //Navigation Property
    public Category Category { get; set; }
}
```

>[!NOTE] One-to-One

Example : One user can have only one User profile.

```cs
public class User
{
    public int Id { get; set; }
    public UserProfile Profile { get; set;}
}
```

```cs
public class UserProfile
{
    public int Id { get; set; }
    public int UserId { get; set; }
    public User User { get; set; }
}
```

>[!NOTE] Many-to-Many

Example : A students can enrol in multiple courses, A course can belong to multiple students. Basically many students can have many courses.

```cs
public class Student
{
    public int Id { get; set; }
    public ICollection<Course> Courses{ get; set;}
}
```

```cs
public class Course
{
    public int Id { get; set; }
    public ICollection<Student> Students { get; set; }
}
```
---
>[!question] Lazy Loading vs Eager Loading

>[!NOTE] Eager Loading :

Load everything immediately. Eager loading loads related entities as part of the initial query.

```cs
var products = await _context.Products
        .Include(p => p.Category)
        .ToListAsync();
```

Generated SQL

```sql
SELECT *
FROM Products p
JOIN Categories c
```

Include() : JOIN FETCH from Hibernate

ThenInclude() :  ThenInclude loads nested related entities after an Include operation.

```cs
var orders =
    await _context.Orders
        .Include(o => o.OrderItems)
        .ThenInclude(i => i.Product)
        .ToListAsync();
```

---------

>[!NOTE] Lazy Loading :

Lazy loading loads related entities only when they are first accessed.

```  cs
var product =
    await _context.Products
                  .FirstAsync();
```

Later: 

``` cs
product.Category
```
---

 >[!Question] N+1 Problem :

N+1 occurs when loading related entities individually, resulting in excessive database queries.


suppose we run 1 query for products 

```cs
var products =
    await _context.Products
                  .ToListAsync();
```

returns 100 products

100 queries for categories

```cs
foreach(var p in products)
{
    Console.WriteLine(
        p.Category.Name);
}
```



Total: 101 queries. this is N+1 Problem


---
>[!Question] Data Annotations vs Fluent API?

> Data Annotations are simple attribute-based configurations, while Fluent API provides more powerful and flexible configuration options.

```cs
[StringLength(100)]

//---vs---

modelBuilder.Entity<Product>()
    .Property(...)
```