## Entity 


```cs
namespace ProductManagement.Api.Entities;

public class Product {

	//EF Core automatically treats `Id` or `<EntityName>Id` as the primary key.
	public int Id { get; set; }
	public string Name { get; set; } = string.Empty;
	public string Description { get; set; } = string.Empty;
	public decimal Price { get; set; }
	public string ImageUrl { get; set; } = string.Empty;
	public int Stock { get; set; }
	public DateOnly ExpiryDate { get; set; }

}
```

---
## DTOs

### Request DTOs


```cs
namespace ProductManagement.Api.DTOs.Requests;

public class UpdateProductRequest{
	
	public string Name { get; set; } = string.Empty;
	public string Description { get; set; } = string.Empty;
	public decimal Price { get; set; }
	public string ImageUrl { get; set; } = string.Empty;
	public int Stock { get; set; }
	public DateOnly ExpiryDate { get; set; }
	
}
```


```cs
namespace ProductManagement.Api.DTOs.Requests;
public class CreateProductRequest {

	// No id cause database autometically creates it not the client
	public string Name { get; set; } = string.Empty;
	public string Description { get; set; } = string.Empty;
	public decimal Price { get; set; }
	public string ImageUrl { get; set; } = string.Empty;
	public int Stock { get; set; }
	public DateOnly ExpiryDate { get; set; }

}
```

Response DTO

```cs
namespace ProductManagement.Api.DTOs.Responses;
public class ProductResponse {


	//In response we include `Id` cause the client needs it
	public int Id { get; set; }
	public string Name { get; set; } = string.Empty;
	public string Description { get; set; } = string.Empty;
	public decimal Price { get; set; }
	public string ImageUrl { get; set; } = string.Empty;
	public int Stock { get; set; }
	public DateOnly ExpiryDate { get; set; }
	
}
```
---
## Mapper


```cs
using ProductManagement.Api.DTOs.Requests;
using ProductManagement.Api.DTOs.Responses;
using ProductManagement.Api.Entities;

namespace ProductManagement.Api.Mappers;
  

public static class ProductMapper {

// CreateProductRequest -> Product
	public static Product ToEntity(CreateProductRequest request){
	return new Product{
		Name = request.Name,
		Description = request.Description,
		Price = request.Price,
		ImageUrl = request.ImageUrl,
		Stock = request.Stock,
		ExpiryDate = request.ExpiryDate
	};

}


// Product -> ProductResponse
public static ProductResponse ToResponse( Product product){
	return new ProductResponse {

		Id = product.Id,
		Name = product.Name,
		Description = product.Description,
		Price = product.Price,
		ImageUrl = product.ImageUrl,
		Stock = product.Stock,	
		ExpiryDate = product.ExpiryDate

	};

}

// Update existing Product from UpdateProductRequest

public static void UpdateEntity(Product product, UpdateProductRequest request){

		product.Name = request.Name;
		product.Description = request.Description;
		product.Price = request.Price;
		product.ImageUrl = request.ImageUrl;
		product.Stock = request.Stock;
		product.ExpiryDate = request.ExpiryDate;
	}

}
```

---

## AppDBContext.cs

```cs
using Microsoft.EntityFrameworkCore;
using ProductManagement.Api.Entities;


namespace ProductManagement.Api.Data;

  
// DbContext == primary EF Core class responsible for managing database connections, tracking entities, and executing database operations.

// DbContext already provides Repository and Unit of Work functionality, so an additional repository layer is optional.

public class AppDbContext : DbContext {
	
	public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) {

	}


	//DbSet == database table and provides querying and CRUD capabilities.
	// JpaRepository<Product,Integer>
	public DbSet<Product> Products{get;set;}

	}
```

---
## Controller


```cs
using Microsoft.AspNetCore.Mvc;
using ProductManagement.Api.DTOs.Requests;
using ProductManagement.Api.Services.Interfaces;

namespace ProductManagement.Api.Controllers;

  

// Marks this class as a REST API Controller. similar @RestController
[ApiController]

// Base URL: @RequestMapping
[Route("api/products")]

public class ProductController : ControllerBase {

		// Constructor Dependency Injection.
	private readonly IProductService _productService;
		
	public ProductController(IProductService productService){
		_productService = productService;
	}
	
	  
	// GET /api/products
	//IActionResult == ResponseEntity. Represents HTTP responses
	[HttpGet]
	public async Task<IActionResult>GetAllProducts(){
		var products = await _productService.GetAllProducts();
		return Ok(products);
	}
	
	  
	// GET /api/products/1
	[HttpGet("{id}")]
	public async Task<IActionResult> GetProductById(int id) {
	
		var product = await _productService.GetProductById(id);
		return Ok(product);
	}
	
	
	// POST /api/products
	[HttpPost]
	public async Task<IActionResult> CreateProduct(CreateProductRequest request){
		
		var product = await _productService.CreateProduct(request);
		return Ok(product);
	}
	
	
	// PUT /api/products/1
	[HttpPut("{id}")]
	public async Task<IActionResult> UpdateProduct(
			int id, 
			UpdateProductRequest request
			){
	
		var product = await _productService.UpdateProduct(id, request);
		return Ok(product);
	}
	
	// DELETE /api/products/1
	
	[HttpDelete("{id}")]
	public async Task<IActionResult> DeleteProduct(int id) {
	
		var product = await _productService.DeleteProduct(id);
		return Ok(product);
	}
}

```

---
## service Interface

```cs
using ProductManagement.Api.DTOs.Requests;
using ProductManagement.Api.DTOs.Responses;

namespace ProductManagement.Api.Services.Interfaces;


public interface IProductService {

	// `Task` : It represents a future response of an async task.
	Task<ProductResponse> CreateProduct(CreateProductRequest request);

	Task<ProductResponse> GetProductById(int id);

	Task<List<ProductResponse>> GetAllProducts();

	Task<ProductResponse> UpdateProduct(int id, UpdateProductRequest request);
	
	Task<ProductResponse> DeleteProduct(int id);

}
```

---
## service class 

```cs
using Microsoft.EntityFrameworkCore;
using ProductManagement.Api.Data;
using ProductManagement.Api.DTOs.Requests;
using ProductManagement.Api.DTOs.Responses;
using ProductManagement.Api.Entities;
using ProductManagement.Api.Mappers;
using ProductManagement.Api.Services.Interfaces;

namespace ProductManagement.Api.Services;

  
// Service contains all business logic. Similar to a Spring Boot @Service class.

public class ProductService : IProductService {

// AppDbContext is the EF Core entry point for database operations. similar to Hibernate's EntityManager.
	private readonly AppDbContext _context;
	
	public ProductService(AppDbContext context) {
		_context = context;
	}
	
	
	//------------------------------------------------------

  public async Task<ProductResponse> CreateProduct(CreateProductRequest request) {

// Convert Request DTO -> Entity
		Product pro = ProductMapper.ToEntity(request);

// DbSet<Product> represents the Products table.
// Add() DOES NOT execute SQL immediately. EF Core Starts tracking this object and mark it as Added. Entity State: Added

		_context.Products.Add(pro);
// SaveChangesAsync() looks at all tracked entities.
// Since pro is in Added state, EF generates an INSERT statement. Actual SQL execution happens here.
		await _context.SaveChangesAsync();
// Convert Entity -> Response DTO
		return ProductMapper.ToResponse(pro);

	}

  	   //------------------------------------------------------
  

	public async Task<ProductResponse> GetProductById(int id){
		// FindAsync() searches using the Primary Key.
		// Similar to: repository.findById(id)
		Product? pro = await _context.Products.FindAsync(id);
		if (pro == null) {
		
		// using Custom exceptions instead of Predefined `Exception`
			//throw new Exception( $"Product not found with id {id}");
			throw new ProductNotFoundException( $"Product not found with id {id}");

		}
		
		return ProductMapper.ToResponse(pro);
	}

  
	   //------------------------------------------------------

	public async Task<List<ProductResponse>> GetAllProducts(){
		
		// Executes: SELECT * FROM Products
		List<Product> pros = await _context.Products.ToListAsync();
		// Convert "List<Product>" -> "List<ProductResponse>"
		return pros.Select(ProductMapper.ToResponse).ToList();
	}


  //------------------------------------------------------
  

	public async Task<ProductResponse> UpdateProduct (int id,UpdateProductRequest request) {

	// Load Product from database.
	// EF Core starts tracking the entity. Initial State: Unchanged

	Product? pro = await _context.Products.FindAsync(id);
		if (pro == null){
			throw new ProductNotFoundException($"Product not found with id {id}");
		}

	// Update entity properties. EF Core detects property changes automatically.
		ProductMapper.UpdateEntity(pro, request);

		// No Add() required as Entity is already being tracked.
	//EF sees: Original Value != New Value. State becomes : Modified
		await _context.SaveChangesAsync();

		// EF generates: UPDATE Products
		return ProductMapper.ToResponse(pro);

}

  //------------------------------------------------------
  

	public async Task<ProductResponse> DeleteProduct(int id){
	
	// Load Product from database. Entity State: Unchanged
		Product? pro = await _context.Products.FindAsync(id);
			if (pro == null){
				throw new ProductNotFoundException($"Product not found with id {id}");
		}

		// Remove() DOES NOT execute SQL immediately. It just marks the entity State as: Deleted

		_context.Products.Remove(pro);
// SaveChangesAsync() sees: Product State = Deleted, then EF runs the delete query
		await _context.SaveChangesAsync();

		return ProductMapper.ToResponse(pro);

}

}
```


---
## Global Exception Handling

### Creating a Custom Exception and Handle it 


```cs
namespace ProductManagement.Api.Exceptions;


// Thrown when a requested Product does not exist.
public class ProductNotFoundException : Exception {
	public ProductNotFoundException( string message) : base(message) {
	
	}

}
```

Without Custom Exception : It will throw a generalised error and status code 

```cs
throw new Exception($"Product not found with id {id}");
```


With Custom Exception : proper exception handling and proper status code

```cs
throw new ProductNotFoundException($"Product not found with id {id}");
```



---