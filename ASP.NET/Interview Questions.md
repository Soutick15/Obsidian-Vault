


- Explain service lifetimes.
- Why is DbContext Scoped?
- Explain Middleware.
- Explain Routing and Model Binding.
- IActionResult vs ActionResult<T.
- What does `[ApiController]` do?
- Explain validation using Data Annotations.
- Explain Global Exception Handling.
- Explain DbContext and DbSet.
- What happens when you call `SaveChangesAsync()`?
- Explain EF Core Change Tracking.
- Explain Migrations.
- Explain CORS.
- Explain your project's architecture.
- Walk through your Product Create API from request to database.
- Repository Pattern—when would you use it, and when might you avoid it?

---
# ⭐⭐⭐⭐⭐ Priority 1 — Must Know (Almost Guaranteed)

## 1. C# Fundamentals

- Explain the .NET platform and how a C# program executes.
- What is CLR?
- What is CTS?
- What is CLS?
- What is IL (Intermediate Language/MSIL)?
- What is JIT Compilation?
- What is an Assembly?
- Difference between EXE and DLL.
- Value Type vs Reference Type.
- Stack vs Heap.
- Boxing vs Unboxing.
- Managed vs Unmanaged Code.
- Garbage Collection.
- `var` vs explicit type.
- `const` vs `readonly`.
- `class` vs `record`.
- `abstract class` vs `interface`.
- `virtual` vs `override`.
- `sealed` class.
- Extension Methods.
- Nullable Reference Types.
- `using` statement.

---

## 2. Delegates & Functional Programming

- What is a Delegate?
- Why use Delegates?
- What is `Func<>`?
- What is `Action<>`?
- What is `Predicate<>`?
- Lambda Expressions.
- Anonymous Methods.
- Events and EventHandler.

---

## 3. LINQ

- What is LINQ?
- LINQ vs Java Streams.
- `Where()`
- `Select()`
- `OrderBy()`
- `OrderByDescending()`
- `GroupBy()`
- `Join()`
- `Any()`
- `All()`
- `Count()`
- `First()`
- `FirstOrDefault()`
- `Single()`
- `SingleOrDefault()`
- `Skip()`
- `Take()`
- Deferred Execution.
- Immediate Execution.
- `IEnumerable` vs `IQueryable`.

---

## 4. Async Programming

- What is asynchronous programming?
- Why use `async`/`await`?
- What is `Task`?
- What is `Task<T>`?
- Thread vs Task.
- Does `await` block the thread?
- Exception handling with async.
- When should async be used?
- `ConfigureAwait()` (basic understanding).

---

# ⭐⭐⭐⭐⭐ Priority 2 — ASP.NET Core

## 5. ASP.NET Core Fundamentals

- What is ASP.NET Core?
- ASP.NET Core vs ASP.NET Framework.
- ASP.NET Core Architecture.
- Request Lifecycle.
- `Program.cs`.
- Hosting Model.
- Middleware Pipeline.
- RequestDelegate.
- HttpContext.

---

## 6. Dependency Injection

- What is DI?
- Why use DI?
- Constructor Injection.
- Service Registration.
- `AddScoped()`
- `AddSingleton()`
- `AddTransient()`
- Difference between Scoped, Singleton and Transient.
- Why is `DbContext` Scoped?

---

## 7. Controllers & Routing

- What is `[ApiController]`?
- `Controller` vs `ControllerBase`.
- Routing.
- Attribute Routing.
- Conventional Routing.
- HTTP Verbs.
- `IActionResult`.
- `ActionResult<T>`.
- Model Binding.
- `[FromBody]`
- `[FromRoute]`
- `[FromQuery]`
- `[FromHeader]`

---

## 8. Middleware

- What is Middleware?
- Request Pipeline.
- `Use()`
- `Run()`
- `Map()`
- Custom Middleware.
- Exception Middleware.
- Authentication Middleware.
- Middleware execution order.

---

## 9. Validation

- Data Annotations.
- `[Required]`
- `[StringLength]`
- `[Range]`
- `[EmailAddress]`
- Model Validation.
- What does `[ApiController]` do?
- FluentValidation (basic comparison).

---

## 10. Exception Handling

- Global Exception Handling.
- Custom Exceptions.
- Exception Middleware.
- Why not use try-catch everywhere?
- Producing consistent error responses.

---

# ⭐⭐⭐⭐⭐ Priority 3 — Entity Framework Core

## 11. DbContext

- What is DbContext?
- What is DbSet?
- DbContext Lifecycle.
- Change Tracking.
- Entity States:
    - Added
    - Modified
    - Deleted
    - Unchanged
    - Detached

---

## 12. CRUD Operations

- `Add()`
- `Update()`
- `Remove()`
- `FindAsync()`
- `ToListAsync()`
- `SaveChangesAsync()`
- What happens inside `SaveChanges()`?

---

## 13. Relationships

- One-to-One.
- One-to-Many.
- Many-to-Many.
- Foreign Keys.
- Navigation Properties.
- Fluent API vs Data Annotations.

---

## 14. Querying

- LINQ to Entities.
- `Include()`
- Eager Loading.
- Lazy Loading.
- Explicit Loading.
- `AsNoTracking()`
- Tracking vs No Tracking.
- N+1 Query Problem.

---

## 15. Migrations

- What is Migration?
- Why use Migrations?
- Model Snapshot.
- `dotnet ef migrations add`
- `dotnet ef database update`
- Difference from Flyway/Liquibase.

---

# ⭐⭐⭐⭐⭐ Priority 4 — Security

## 16. Authentication & Authorization

- Authentication vs Authorization.
- Cookie Authentication.
- JWT Authentication.
- Session Authentication.
- Stateless Authentication.
- JWT Structure.
- Claims.
- Bearer Token.
- Secret Key.
- Token Expiration.
- Refresh Token.
- `[Authorize]`
- Roles.
- Policies.

---

## 17. CORS

- What is CORS?
- Why is it needed?
- How do you configure it?
- When should credentials be allowed?

---

# ⭐⭐⭐⭐ Priority 5 — Architecture

## 18. API Design

- REST Principles.
- HTTP Methods.
- Status Codes.
- Pagination.
- Sorting.
- Filtering.
- API Versioning (basic understanding).

---

## 19. Layered Architecture

- Controller Layer.
- Service Layer.
- Repository Layer.
- DTO Layer.
- Entity Layer.
- Mapper Layer.
- Why separate responsibilities?

---

## 20. DTOs & Mapping

- DTO vs Entity.
- Why DTOs?
- Why not expose Entities?
- Manual Mapping.
- AutoMapper (basic knowledge).

---

## 21. Repository Pattern

- What is Repository Pattern?
- Why use it?
- Does EF Core already implement it?
- Unit of Work.
- When should you skip a Repository layer?

---

## 22. SOLID Principles

- SRP
- OCP
- LSP
- ISP
- DIP

You don't need textbook definitions—be able to explain how they influence backend design.

---

## 23. Clean Architecture

- Layers.
- Dependency Rule.
- Domain.
- Application.
- Infrastructure.
- Presentation.

---

# ⭐⭐⭐ Priority 6 — Configuration & Deployment

## 24. Configuration

- `appsettings.json`
- Environment-specific configuration.
- `IConfiguration`
- Options Pattern (`IOptions<T>`)
- Environment Variables.
- Secret Management.

---

## 25. Swagger/OpenAPI

- What is OpenAPI?
- Swagger.
- API Documentation.
- Testing APIs.

---

## 26. Docker (Basic)

- What is Docker?
- Image.
- Container.
- Dockerfile.
- Port Mapping.
- Why Docker?

---

# ⭐⭐⭐ Priority 7 — Database

- Transactions.
- ACID.
- Indexes.
- Connection Pooling.
- Optimistic Concurrency (basic).
- PostgreSQL basics.

---

# ⭐⭐ Priority 8 — Microservices

- Monolith vs Microservices.
- Event-Driven Architecture.
- API Gateway.
- Service Discovery (basic).
- Message Brokers (Kafka/RabbitMQ basics).

---

# ⭐⭐ Priority 9 — Nice to Know

- Logging (`ILogger`)
- Caching (In-Memory, Distributed)
- Localization
- Globalization
- Health Checks
- Background Services (`IHostedService`)

>[!question] What are security controls available on ASP.NET?

Following are the five security controls available on ASP.NET:

- `<asp: Login>` Provides a login capability that enables the users to enter their credentials with ID and password fields.
- `<asp: LoginName>` Used to display the user name who has logged-in.
- `<asp: LoginView>` Provides a variety of views depending on the template that has been selected.
- `<asp: LoginStatus>` Used to check whether the user is authenticated or not.
- `<asp: PasswordRecovery>` Sends an email to a user while resetting the password.


>[!question] What is MIME in .NET?

MIME stands for `Multipurpose Internet Mail Extensions`. It is the extension of the e-mail protocol which lets users use the protocol to exchange files over emails easily.

Servers insert the MIME header at the beginning of the web transmission to denote that it is a MIME transaction.

Then the clients use this header to select an appropriate ‘player’ for the type of data that the header indicates. Some of these players are built into the web browser.


>[!question]  What is the use of manifest in the .NET framework?

Manifest stores the metadata of the assembly. It contains metadata which is required for many things as given below:

- Assembly version information.
- Scope checking of the assembly.
- Reference validation to classes.
- Security identification.

>[!question] Explain different types of cookies available in ASP.NET?

Two types of cookies are available in ASP.NET. They are:

- **Session Cookie:** It resides on the client machine for a single session and is valid until the user logs out.
- **Persistent Cookie:** It resides on the user machine for a period specified for its expiry. It may be an hour, a day, a month, or never.
>[!question]  What is the meaning of CAS in .NET?


Code Access Security(CAS) is necessary to prevent unauthorized access to programs and resources in the runtime. It is designed to solve the issues faced when obtaining code from external sources, which may contain bugs and vulnerabilities that make the user’s system vulnerable.

CAS gives limited access to code to perform only certain operations instead of providing all at a given point in time. CAS constructs a part of the native .NET security architecture.

>[!question]  Explain localization and globalization.

Localization is the process of customizing our application to behave as per the current culture and locale.

Globalization is the process of designing the application so that it can be used by users from across the globe by supporting multiple languages.


>[!question]  What are MDI and SDI?

**MDI (Multiple Document Interface):** An MDI allows you to open multiple windows, it will have one parent window and as many child windows. The components are shared from the parent window like toolbar, menubar, etc.

**SDI (Single Document Interface):** SDI opens each document in a separate window. Each window has its own components like a toolbar, menubar, etc. Therefore it is not constrained to the parent window.


### What is CoreCLR?

### What is the purpose of webHostBuilder()?

WebHostBuilder function is used for HTTP pipeline creation through `webHostBuilder.Use()` chaining all at once with `WebHostBuilder.Build()` by using the builder pattern. This function is provided by `Microsoft.AspNet.Hosting namespace`. The Build() method’s purpose is building necessary services and a `Microsoft.AspNetCore.Hosting.IWebHost` for hosting a web application.


### What is Zero Garbage Collectors?

Zero Garbage Collectors allows you for object allocation as this is required by the Execution Engine. Created objects will not get deleted automatically and theoretically, no longer required memory is never reclaimed.

There are two main uses of Zero Garbage Collectors. They are:

- Using this, you can develop your own Garbage Collection mechanism. It provides the necessary functionalities for properly doing the runtime work.
- It can be used in special use cases like very short living applications or almost no memory allocation(concepts such as No-alloc or Zero-alloc programming). In these cases, Garbage Collection overhead is not required and it is better to get rid of it.