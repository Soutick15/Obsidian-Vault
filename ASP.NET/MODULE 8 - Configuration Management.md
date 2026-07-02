To set up a Spring Boot project we need to do some Configuration like 

```
Database URL
Database Username
Database Password

JWT Secret

AWS Credentials

Redis Configuration

External API URLs

Feature Flags
```


We usually do these configuration in 

|Spring Boot|ASP.NET Core|
|---|---|
|application.properties|appsettings.json|
|application.yml|appsettings.json|
|@Value|IConfiguration|
|@ConfigurationProperties|Options Pattern|
|profiles|appsettings.Development.json|

ASP.NET Core Equivalent  :  appsettings.json

`appsettings.json`

```json 
{
  "ConnectionStrings": {
    "DefaultConnection":
      "Host=localhost;Port=5432;Database=ProductDb;Username=postgres;Password=admin"
  },

  "JwtSettings": {
    "SecretKey": "my-secret-key",
    "Issuer": "ProductApi",
    "Audience": "ProductApiUsers"
  }
}
```

`IConfiguration` 

suppose 
```json
{
  "AppSettings": {
    "AppName": "Product API"
  }
}
```
Inject configuration

```c#
public class ProductService
{
    private readonly IConfiguration _configuration;

    public ProductService(IConfiguration configuration)
    {
        _configuration = configuration;
    }
}
```

read value 

```c#
string appName = _configuration["AppSettings:AppName"];
```