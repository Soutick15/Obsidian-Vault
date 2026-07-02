
- `.NET framework` is developed by Microsoft, provides an environment to run, debug and deploy code onto web services and applications by using tools and functionalities like libraries, classes, and APIs.
- `.NET Core` is a newer version of the .NET framework and it is open-source, platform independent, and can be used to develop various kinds of applications like mobile, web, IoT, cloud, microservices, machine learning, game, etc.

ASP.NET Core is Microsoft's framework for :

- REST APIs
- Microservices
- Web Applications
- Cloud Applications

Unlike `Java` we will not install `C#` language version. We need to install `.NET SDK` to run `.NET` application. because the `SDK` determines which `C# compiler` is available.

>[!EXAMPLE] ` .NET SDK` contains 
>- `C#` Compiler 
>- `.NET` Runtime
>- `.NET` CLI
>- Project Templates
>- Build Tools

```bash

	#install .NET SDK
	brew install --cask dotnet-sdk

	--dotnet version
	#output : 10.0.301
	
	dotnet --list-sdks
	#output :10.0.301 [/usr/local/share/dotnet/sdk]
```

Once `.NET SDK` is available in our system, we will create a simple `C#` project. 
from the console run this :

```bash
# Create a simple project called `HelloWorldDotNet`
dotnet new console -n HelloWorldDotNet
	
# Go inside of the project 
cd HelloWorldDotNet 
	
# To run the application
dotnet run 
```

>[!NOTE] `dotnet new console`

- This is a simple `HelloWorldDotNet` project we created. 
- It is good for learning core `C#` , Practice LINQ , Practice Async/Await, Practice OOP etc. 
- It does not contain any web server, APIs, database. 
- Generates structure :

```text
	HelloWorldDotNet
	│
	├── Program.cs
	├── HelloWorldDotNet.csproj
```

>[!NOTE]  `dotnet new webapi`

>But for real life we need a complete ASP.NET Core API project, where we want to build REST APIs, do dependency Injection, Middleware, EF Core, implement JWT, Swagger and much more.
>
>Run this from terminal to create a complete project structure : 

```bash
#create a complete project called `ProductManagement`
dotnet new webapi -n ProductManagement.Api

# Go inside of the project 
cd HelloWorldDotNet 
	
# To run the application
dotnet run 
```

When we create a project using `dotnet new webapi` the `.NET SDK` will internally create 
- Creates project structure
- Creates `.csproj`
- Creates Program.cs
- Adds Swagger setup
- Configures Dependency Injection
- Configures Kestrel server

It will create a complete project

```text
ProductManagement.Api
│
├── Program.cs
├── appsettings.json
├── appsettings.Development.json
├── ProductManagement.Api.csproj
├── Properties
│
└── Controllers (sometimes)
```

Now lets understand the generated files one by one :

  > [!INFO] `Program.cs`   ≈ @SpringBootApplication / main() method
  
> It is the application's entry point where services are registered, middleware is configured, and the web host is started. It is equivalent to main() method in SpringBoot. 
 >  
 >In springBoot when we use annotations like `@Service`, `@Repository`, `@Component` etc, internally Spring automatically registers these classes in the DI Container without any manual registration. 
 >
 >But in .NET we need to manually register `Controllers`, `Services`, `Database`, `Authentication`, `Logging` etc. in the `Program.cs` file. 

```cs
//Create application configuration. 
var builder = WebApplication.CreateBuilder(args);

//Registers Controllers
builder.Services.AddControllers();

//Build application
var app = builder.Build();

// It maps URL to Controller class. (api/products  to ProductController)
app.MapControllers();

//Start Kestrel Web Server
app.Run();
```

---
  > [!INFO] `appsettings.json`  ≈ application.yml / application.properties

> `appsettings.json` is the primary configuration file used by ASP.NET Core applications.
> It is used for 
- Database Config
- JWT Config
- API Keys
- Logging Config
- Application Settings

```json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information"
    }
  }
}
```

---
  > [!INFO] `appsettings.Development.json`  ≈ application-dev.yml / application-dev.properties
  
 >Development-specific settings. `ASP.NET` automatically loads it when: Environment = Development
 >
 >It is used to override configuration values for the development environment without affecting production settings.

```json
{
  "Logging": {
    "LogLevel": {
      "Default": "Debug"
    }
  }
}
```
---
>[!INFO] `ProductManagement.Api.csproj` ≈ pom.xml

> The `.csproj` file defines project metadata & dependencies, target framework, package references, and build settings.

```json

<Project Sdk="Microsoft.NET.Sdk.Web">

  <PropertyGroup>
    <TargetFramework>
      net10.0
    </TargetFramework>
  </PropertyGroup>

</Project>
```

---
>[!INFO] `/Properties/launchSettings.json`

It controls : Ports, Launch Profiles, Environment Variables

```json
{
  "profiles": {
    "http": {
      "applicationUrl":
      "http://localhost:5047"
    }
  }
}
```
---
>[!INFO]  `/bin` folder

After dotnet builds the application, the `bin` folder contains Compiled DLLs, Executables, Dependencies. 

---
>[!info]  `ProductManagement.Api.http`

It is used to test APIs directly from IDE. Similar to Postman Collection but file-based.

---

>[!info] `NuGet` ≈ Maven

NuGet downloads the project libraries according to the dependencies added in `.csproj` file.

>[!info] `Kestrel` ≈ Tomcat

In ASP.NET Core `Kestrel` is the default embedded web server to handle HTTP requests.