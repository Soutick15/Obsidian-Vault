
>[!QUESTION] Why Logging is required?

In production system if any of our API is failing, without logs we don't know why it is failing. With logs we can identify the actual problem :

ProductService
↓
Database Timeout
↓
PostgreSQL Connection Error

In ASP.NET Core we use Built-in logging :

```cs
ILogger<T>
```

Injecting logger :

```cs
public class ProductService{
    private readonly ILogger<ProductService> _logger;

    public ProductService( ILogger<ProductService> logger){
        _logger = logger;
    }
}
```

```cs
//Normal application event
_logger.LogInformation("Product Created");

//Something unusual, but application still works
_logger.LogWarning("Product stock is low");

//Something failed
_logger.LogError("Database Connection Failed");

//Major failure
_logger.LogCritical("Application cannot continue");
```

Java comparison:

```java
private static final Logger log = LoggerFactory.getLogger( ProductService.class);
```

---
>[!note] Structured Logging :

> Structured logging stores log data as key-value pairs rather than plain text, making logs easier to search and analyze.

```cs
public async Task<Product> GetProductById(int id){

	//Structured Logging using {Id}
    _logger.LogInformation("Fetching Product {Id}", id);
    
    return await _context.Products.FindAsync(id);
}
```

---

Create Custom Exception : 

```cs
public class ProductNotFoundException : Exception {
    public ProductNotFoundException( string message) : base(message){
    }
}
```

Throw this custom Exception :

```cs
throw new ProductNotFoundException($"Product {id} not found");
```

>[!info] Global Exception Handling in ASP.NET Core is handled using the Global Exception Middleware 

