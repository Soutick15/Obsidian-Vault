

MODULE 1
.NET Ecosystem Fundamentals

MODULE 2
C# Fundamentals

MODULE 3
Object Oriented Programming in C#

MODULE 4
Delegates, Events, Lambda Expressions

MODULE 5
LINQ

MODULE 6
Async Programming

MODULE 7
ASP.NET Core Fundamentals

MODULE 8
Dependency Injection

MODULE 9
Configuration Management

MODULE 10
Controllers & APIs

MODULE 11
Middleware Pipeline

MODULE 12
Entity Framework Core

MODULE 13
Validation

MODULE 14
Logging

MODULE 15
Exception Handling

MODULE 16
Authentication & JWT

MODULE 17
Architecture Patterns

MODULE 18
Build Product Management System

			Features:
			- Product CRUD
			- PostgreSQL
			- EF Core
			- DTOs
			- Validation
			- Global Exception Handling
			- Logging
			- JWT Authentication
			- Swagger
			- Clean Architecture

MODULE 19
Interview Preparation


Request Pipeline
Middleware
Use()
Run()
Map()
Custom Middleware
Global Exception Middleware
Middleware Ordering




>[!QUESTION] Open questions to ask later

- How actually we add dependencies? In the product management project we did it via terminal. Do we have anything similar like maven repository? Or we have both the options which ever we can follow?

```bash
   ~/Downloads/Practice Dot Net/ProductManagement.Api ❯ dotnet add package Microsoft.EntityFrameworkCore
info : X.509 certificate chain validation will use the fallback certificate bundle at '/usr/local/share/dotnet/sdk/10.0.301/trustedroots/codesignctl.pem'.
info : X.509 certificate chain validation will use the fallback certificate bundle at '/usr/local/share/dotnet/sdk/10.0.301/trustedroots/timestampctl.pem'.
info : Adding PackageReference for package 'Microsoft.EntityFrameworkCore' into project '/Users/souticksamanta/Downloads/Practice Dot Net/ProductManagement.Api/ProductManagement.Api.csproj'.
info :   GET https://api.nuget.org/v3/registration5-gz-semver2/microsoft.entityframeworkcore/index.json
info :   OK https://api.nuget.org/v3/registration5-gz-semver2/microsoft.entityframeworkcore/index.json 237ms
info :   GET https://api.nuget.org/v3/registration5-gz-semver2/microsoft.entityframeworkcore/page/0.0.1-alpha/3.1.2.json
info :   OK https://api.nuget.org/v3/registration5-gz-semver2/microsoft.entityframeworkcore/page/0.0.1-alpha/3.1.2.json 240ms
info :   GET https://api.nuget.org/v3/registration5-gz-semver2/microsoft.entityframeworkcore/page/3.1.3/6.0.0-preview.6.21352.1.json
info :   OK https://api.nuget.org/v3/registration5-gz-semver2/microsoft.entityframeworkcore/page/3.1.3/6.0.0-preview.6.21352.1.json 239ms
info :   GET https://api.nuget.org/v3/registration5-gz-semver2/microsoft.entityframeworkcore/page/6.0.0-preview.7.21378.4/7.0.17.json
info :   OK https://api.nuget.org/v3/registration5-gz-semver2/microsoft.entityframeworkcore/page/6.0.0-preview.7.21378.4/7.0.17.json 239ms
info :   GET https://api.nuget.org/v3/registration5-gz-semver2/microsoft.entityframeworkcore/page/7.0.18/9.0.14.json
info :   OK https://api.nuget.org/v3/registration5-gz-semver2/microsoft.entityframeworkcore/page/7.0.18/9.0.14.json 350ms
info :   GET https://api.nuget.org/v3/registration5-gz-semver2/microsoft.entityframeworkcore/page/9.0.15/11.0.0-preview.5.26302.115.json
info :   OK https://api.nuget.org/v3/registration5-gz-semver2/microsoft.entityframeworkcore/page/9.0.15/11.0.0-preview.5.26302.115.json 304ms
info : Restoring packages for /Users/souticksamanta/Downloads/Practice Dot Net/ProductManagement.Api/ProductManagement.Api.csproj...
info :   GET https://api.nuget.org/v3-flatcontainer/microsoft.entityframeworkcore/index.json
info :   OK https://api.nuget.org/v3-flatcontainer/microsoft.entityframeworkcore/index.json 22ms
info :   GET https://api.nuget.org/v3-flatcontainer/microsoft.entityframeworkcore/10.0.9/microsoft.entityframeworkcore.10.0.9.nupkg
info :   OK https://api.nuget.org/v3-flatcontainer/microsoft.entityframeworkcore/10.0.9/microsoft.entityframeworkcore.10.0.9.nupkg 15ms
info :   GET https://api.nuget.org/v3-flatcontainer/microsoft.entityframeworkcore.abstractions/index.json
info :   GET https://api.nuget.org/v3-flatcontainer/microsoft.entityframeworkcore.analyzers/index.json
info :   OK https://api.nuget.org/v3-flatcontainer/microsoft.entityframeworkcore.analyzers/index.json 17ms
info :   GET https://api.nuget.org/v3-flatcontainer/microsoft.entityframeworkcore.analyzers/10.0.9/microsoft.entityframeworkcore.analyzers.10.0.9.nupkg
info :   OK https://api.nuget.org/v3-flatcontainer/microsoft.entityframeworkcore.abstractions/index.json 31ms
info :   GET https://api.nuget.org/v3-flatcontainer/microsoft.entityframeworkcore.abstractions/10.0.9/microsoft.entityframeworkcore.abstractions.10.0.9.nupkg
info :   OK https://api.nuget.org/v3-flatcontainer/microsoft.entityframeworkcore.analyzers/10.0.9/microsoft.entityframeworkcore.analyzers.10.0.9.nupkg 21ms
info :   OK https://api.nuget.org/v3-flatcontainer/microsoft.entityframeworkcore.abstractions/10.0.9/microsoft.entityframeworkcore.abstractions.10.0.9.nupkg 24ms
info : Installed Microsoft.EntityFrameworkCore.Abstractions 10.0.9 from https://api.nuget.org/v3/index.json to /Users/souticksamanta/.nuget/packages/microsoft.entityframeworkcore.abstractions/10.0.9 with content hash GRMaiPkqYna/gCsyDffYDWmefGPC3hDrdMw+2rrGcQwhs6uZOsaMQXMJnoXQ35tx9SkBV2ieRRU9N/jLOO6BZw==.
info : Installed Microsoft.EntityFrameworkCore.Analyzers 10.0.9 from https://api.nuget.org/v3/index.json to /Users/souticksamanta/.nuget/packages/microsoft.entityframeworkcore.analyzers/10.0.9 with content hash aiEFB+C5EsZGqxvMPazE07hbWsp4iPaufJpanGt5O+lrwv7mJLrqma5haVIgFAPCyhQkmk75XSCEubT1zUjxtA==.
info : Installed Microsoft.EntityFrameworkCore 10.0.9 from https://api.nuget.org/v3/index.json to /Users/souticksamanta/.nuget/packages/microsoft.entityframeworkcore/10.0.9 with content hash tu85SRzOT021V7EQlViCiAE7TqldVn469Y6lt5TEn/+XC4/MeNCHgMRSxqYuWqvF4zAQZUhCmtNEZuM3ss4LeA==.
info :   GET https://api.nuget.org/v3/vulnerabilities/index.json
info :   OK https://api.nuget.org/v3/vulnerabilities/index.json 234ms
info :   GET https://api.nuget.org/v3-vulnerabilities/2026.06.18.23.45.47/vulnerability.base.json
info :   GET https://api.nuget.org/v3-vulnerabilities/2026.06.18.23.45.47/2026.06.19.05.45.48/vulnerability.update.json
info :   OK https://api.nuget.org/v3-vulnerabilities/2026.06.18.23.45.47/vulnerability.base.json 235ms
info :   OK https://api.nuget.org/v3-vulnerabilities/2026.06.18.23.45.47/2026.06.19.05.45.48/vulnerability.update.json 234ms
info : Package 'Microsoft.EntityFrameworkCore' is compatible with all the specified frameworks in project '/Users/souticksamanta/Downloads/Practice Dot Net/ProductManagement.Api/ProductManagement.Api.csproj'.
info : PackageReference for package 'Microsoft.EntityFrameworkCore' version '10.0.9' added to file '/Users/souticksamanta/Downloads/Practice Dot Net/ProductManagement.Api/ProductManagement.Api.csproj'.
info : Generating MSBuild file /Users/souticksamanta/Downloads/Practice Dot Net/ProductManagement.Api/obj/ProductManagement.Api.csproj.nuget.g.props.
info : Writing assets file to disk. Path: /Users/souticksamanta/Downloads/Practice Dot Net/ProductManagement.Api/obj/project.assets.json
log  : Restored /Users/souticksamanta/Downloads/Practice Dot Net/ProductManagement.Api/ProductManagement.Api.csproj (in 1.27 sec).   
```

```bash
   ~/Downloads/Practice Dot Net/ProductManagement.Api ❯ dotnet add package Npgsql.EntityFrameworkCore.PostgreSQL
info : X.509 certificate chain validation will use the fallback certificate bundle at '/usr/local/share/dotnet/sdk/10.0.301/trustedroots/codesignctl.pem'.
info : X.509 certificate chain validation will use the fallback certificate bundle at '/usr/local/share/dotnet/sdk/10.0.301/trustedroots/timestampctl.pem'.
info : Adding PackageReference for package 'Npgsql.EntityFrameworkCore.PostgreSQL' into project '/Users/souticksamanta/Downloads/Practice Dot Net/ProductManagement.Api/ProductManagement.Api.csproj'.
info :   GET https://api.nuget.org/v3/registration5-gz-semver2/npgsql.entityframeworkcore.postgresql/index.json
info :   OK https://api.nuget.org/v3/registration5-gz-semver2/npgsql.entityframeworkcore.postgresql/index.json 399ms
info :   GET https://api.nuget.org/v3/registration5-gz-semver2/npgsql.entityframeworkcore.postgresql/page/0.0.1-alpha1/5.0.10.json
info :   OK https://api.nuget.org/v3/registration5-gz-semver2/npgsql.entityframeworkcore.postgresql/page/0.0.1-alpha1/5.0.10.json 240ms
info :   GET https://api.nuget.org/v3/registration5-gz-semver2/npgsql.entityframeworkcore.postgresql/page/6.0.0-preview1/10.0.0-preview.5.json
info :   OK https://api.nuget.org/v3/registration5-gz-semver2/npgsql.entityframeworkcore.postgresql/page/6.0.0-preview1/10.0.0-preview.5.json 240ms
info :   GET https://api.nuget.org/v3/registration5-gz-semver2/npgsql.entityframeworkcore.postgresql/page/10.0.0-preview.7/11.0.0-preview.4.json
info :   OK https://api.nuget.org/v3/registration5-gz-semver2/npgsql.entityframeworkcore.postgresql/page/10.0.0-preview.7/11.0.0-preview.4.json 294ms
info : Restoring packages for /Users/souticksamanta/Downloads/Practice Dot Net/ProductManagement.Api/ProductManagement.Api.csproj...
info :   GET https://api.nuget.org/v3-flatcontainer/npgsql.entityframeworkcore.postgresql/index.json
info :   OK https://api.nuget.org/v3-flatcontainer/npgsql.entityframeworkcore.postgresql/index.json 57ms
info :   GET https://api.nuget.org/v3-flatcontainer/npgsql.entityframeworkcore.postgresql/10.0.2/npgsql.entityframeworkcore.postgresql.10.0.2.nupkg
info :   OK https://api.nuget.org/v3-flatcontainer/npgsql.entityframeworkcore.postgresql/10.0.2/npgsql.entityframeworkcore.postgresql.10.0.2.nupkg 30ms
info :   GET https://api.nuget.org/v3-flatcontainer/microsoft.entityframeworkcore.relational/index.json
info :   GET https://api.nuget.org/v3-flatcontainer/npgsql/index.json
info :   OK https://api.nuget.org/v3-flatcontainer/microsoft.entityframeworkcore.relational/index.json 33ms
info :   GET https://api.nuget.org/v3-flatcontainer/microsoft.entityframeworkcore.relational/10.0.4/microsoft.entityframeworkcore.relational.10.0.4.nupkg
info :   OK https://api.nuget.org/v3-flatcontainer/microsoft.entityframeworkcore.relational/10.0.4/microsoft.entityframeworkcore.relational.10.0.4.nupkg 25ms
info :   OK https://api.nuget.org/v3-flatcontainer/npgsql/index.json 71ms
info :   GET https://api.nuget.org/v3-flatcontainer/npgsql/10.0.3/npgsql.10.0.3.nupkg
info :   OK https://api.nuget.org/v3-flatcontainer/npgsql/10.0.3/npgsql.10.0.3.nupkg 20ms
info : Installed Npgsql.EntityFrameworkCore.PostgreSQL 10.0.2 from https://api.nuget.org/v3/index.json to /Users/souticksamanta/.nuget/packages/npgsql.entityframeworkcore.postgresql/10.0.2 with content hash PsNYgPOSW41Xx19gin7y4EdZAPteWr9Cb01XkdObxOsPzi+mgBupBEN7J7+erXFsROPOILM7MlIoO9QzL8+LGQ==.
info : Installed Microsoft.EntityFrameworkCore.Relational 10.0.4 from https://api.nuget.org/v3/index.json to /Users/souticksamanta/.nuget/packages/microsoft.entityframeworkcore.relational/10.0.4 with content hash DOTjTHy93W3TwpMLM4SCm0n57Sc0Jj3+m2S6LSTstKyBB34eT1UouaMS19mpWwvtj42+sRiEjA3+rOTNoNzXFQ==.
info : Installed Npgsql 10.0.3 from https://api.nuget.org/v3/index.json to /Users/souticksamanta/.nuget/packages/npgsql/10.0.3 with content hash 7nb5YzXuvWWJxB0J8DiyL3we+X4FOctZrt0fIBnucOIaIevFEEwGQVZKtiu9olXdlNAK1eNgqSral6r/jlhI4w==.
info :   CACHE https://api.nuget.org/v3/vulnerabilities/index.json
info :   CACHE https://api.nuget.org/v3-vulnerabilities/2026.06.18.23.45.47/vulnerability.base.json
info :   CACHE https://api.nuget.org/v3-vulnerabilities/2026.06.18.23.45.47/2026.06.19.05.45.48/vulnerability.update.json
info : Package 'Npgsql.EntityFrameworkCore.PostgreSQL' is compatible with all the specified frameworks in project '/Users/souticksamanta/Downloads/Practice Dot Net/ProductManagement.Api/ProductManagement.Api.csproj'.
info : PackageReference for package 'Npgsql.EntityFrameworkCore.PostgreSQL' version '10.0.2' added to file '/Users/souticksamanta/Downloads/Practice Dot Net/ProductManagement.Api/ProductManagement.Api.csproj'.
info : Writing assets file to disk. Path: /Users/souticksamanta/Downloads/Practice Dot Net/ProductManagement.Api/obj/project.assets.json
log  : Restored /Users/souticksamanta/Downloads/Practice Dot Net/ProductManagement.Api/ProductManagement.Api.csproj (in 927 ms).
```

what is this syntax below? specially the constructor? 

```cs
namespace ProductManagement.Api.Exceptions;

// Thrown when a requested Product does not exist.
public class ProductNotFoundException : Exception {
	public ProductNotFoundException( string message) : base(message) {}

}
```

do we use : means it represents the async operation :

```cs
	await with  _context.SaveChangesAsync();
	and without await _context.SaveChanges();
```




Is DBContext == Repository class in SpringBoot ? I dont know what id EntityManager in springBoot

If DbSet represents a Table ? then the Entity also represents a Table. What is the difference. 

Is DBset is same as Entity as DbSet represents a database table and provides querying and CRUD functionality for an entity.?


what are these? is it same like `import java.util.List;` in java

```cs

using Microsoft.EntityFrameworkCore;
using ProductManagement.Api.Entities;
using ProductManagement.Api.DTOs.Requests;

```


what is this? 

```cs

namespace ProductManagement.Api.Services.Interfaces;
```



 Why Not Return ProductResponse Directly? why we are doing
 
```cs

//why we are not following this?
ProductResponse GetProductById(int id);

//why we are following this?
Task<ProductResponse> GetProductById(int id);
```
 


Is there any concept of checked exception and unchecked exception.

The Exception class deep dive









