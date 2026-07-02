- Entity Framework Core is Microsoft's ORM framework that maps `C#` objects to relational database tables.
- It is similar to Hibernate, JPA, Spring Data JPA etc in Java.

| Spring Boot   | ASP.NET Core                       |
| ------------- | ---------------------------------- |
| JPA           | EF Core                            |
| Hibernate     | EF Core                            |
| EntityManager | DbContext                          |
| JpaRepository | DbSet                              |
| @Entity       | Entity                             |
| save()        | SaveChanges(), SaveChangesAsync(), |
| findById()    | FindAsync()                        |
| findAll()     | ToListAsync()                      |
| Flyway        | Migrations                         |

> [!example] Most Important EF Core Components

- Entity
- DbContext
- DbSet
- Migration
- LINQ
- SaveChangesAsync()

---
>[!info] How to add Entity Framework (EF) core in our project

- We know Java doesn't include : Hibernate, JPA, PostgreSQL Driver etc by default. To use these we need to add the dependencies in `pom.xml` .

```XML
<dependency>
    <artifactId> spring-boot-starter-data-jpa </artifactId>
</dependency>

<dependency>
    <artifactId> postgresql </artifactId>
</dependency>
```

- Similarly `ASP.NET` Core itself does not include : `Database Drivers` & `Migration tools`. 
- To add Entity framework in out project run this from Terminal:

```bash

# DB context, DB Set, LINQ, ORM
dotnet add package Microsoft.EntityFrameworkCore

#To work with postgresSQL
dotnet add package Npgsql.EntityFrameworkCore.PostgreSQL

#Migration, DB updates, Schema Generation
dotnet add package Microsoft.EntityFrameworkCore.Tools

#Design Package used by : Migration Engine, Scaffolding, Design-Time Services
dotnet add package Microsoft.EntityFrameworkCore.Design

```

**EntityFrameworkCore provides** : DbContext, DbSet, LINQ Queries, Change Tracking, SaveChanges(), ORM Functionality. 

Then run this to work with postgres SQL : It provides UseNpgsql(), PostgreSQL SQL, Translation, Database Connectivity.

PostgreSQL : 

Install EF Core Tools : To get Migrations, Database Update, Schema Generation. It enables commands like :
	dotnet ef migrations add
	dotnet ef database update


After you install all the above dependencies your `.csproj` file will look like this.

```cs
<Project Sdk="Microsoft.NET.Sdk.Web">

<PropertyGroup>

<TargetFramework>net10.0</TargetFramework>
<Nullable>enable</Nullable>
<ImplicitUsings>enable</ImplicitUsings>

</PropertyGroup>

  
<ItemGroup>

<PackageReference Include="Microsoft.AspNetCore.OpenApi" Version="10.0.9" />
<PackageReference Include="Microsoft.EntityFrameworkCore" Version="10.0.9" />
<PackageReference Include="Microsoft.EntityFrameworkCore.Design" Version="10.0.9">

<IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>

<PrivateAssets>all</PrivateAssets>

</PackageReference>

<PackageReference Include="Microsoft.EntityFrameworkCore.Tools" Version="10.0.9">

<IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>

<PrivateAssets>all</PrivateAssets>

</PackageReference>

<PackageReference Include="Npgsql.EntityFrameworkCore.PostgreSQL" Version="10.0.2" />

</ItemGroup>

</Project>
```

---
> [!NOTE] **Entity :** 

- `Entity` represents Database table. Here’s how we create an Entity class in `C#`.

```C#
public class Product
{

//EF Core automatically treats `Id` or `<EntityName>Id` as the primary key.
    public int Id { get; set; }
    public string Name { get; set; }
    public decimal Price { get; set; }
}
```

Java Entity class for comparison.

```Java
@Entity
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Product {
	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Integer id;
	private String name;
	private Integer price;

}
```


 >Notice we did not mention anything for `Promary Key`. Then how does EF Core identify a primary key? 
 >By convention, EF Core automatically treats a property named `Id` or `<EntityName>Id` as the primary key.
---

> [!NOTE] `DbContext` : ≈ EntityManager

- DbContext is the primary EF Core class represents the entire database session. 
- It is responsible for managing database connections, `tracking entities`, and executing database operations.
- DbContext already provides Repository and Unit of Work functionality, so an additional repository layer is optional.

> [!NOTE] **DbSet** :

DbSet represents a database table and provides querying and CRUD capabilities. 

```cs
public class AppDbContext: DbContext{

    public AppDbContext(DbContextOptions<AppDbContext> options): base(options){
    }

	// DbSet represents `Products` Table
    public DbSet<Product> Products {get; set;}
    
	// DbSet represents `Category` Table
    public DbSet<Category> Categories { get; set; }
    
    // DbSet represents `User` Table
    public DbSet<User> Users { get; set; }
}
```

```java
JpaRepository<Product, Integer>
```

 Register DbContext in `Program`.cs`

```cs
builder.Services.AddDbContext<AppDbContext>(
        options =>
            options.UseNpgsql(
                builder.Configuration
                    .GetConnectionString(
                        "DefaultConnection")));
```

---
>[!INFO] `OpenAPI` ≈ Swagger/ springdoc-openapi

> OpenAPI is a specification used to describe REST APIs in a machine-readable format. ASP.NET Core can automatically generate OpenAPI documentation from controllers and DTOs.



---
### What are Migrations?

> Migrations are version-controlled database schema changes managed by Entity Framework Core.


 Install EF Tool (One-Time Setup)

```bash
#
dotnet tool install --global dotnet-ef

#
dotnet ef                                                        

                     _/\__       
               ---==/    \\      
         ___  ___   |.    \|\    
        | __|| __|  |  )   \\\   
        | _| | _|   \_/ |  //|\\ 
        |___||_|       /   \\\/\\

Entity Framework Core .NET Command-line Tools 10.0.9

Usage: dotnet ef [options] [command]

Options:
  --version        Show version information
  -h|--help        Show help information
  -v|--verbose     Show verbose output.
  --no-color       Don't colorize output.
  --prefix-output  Prefix output with level.

Commands:
  database    Commands to manage the database.
  dbcontext   Commands to manage DbContext types.
  migrations  Commands to manage migrations.

Use "dotnet ef [command] --help" for more information about a command.





dotnet ef migrations add InitialCreate
```
---