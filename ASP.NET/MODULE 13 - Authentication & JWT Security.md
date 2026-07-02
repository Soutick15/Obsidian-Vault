Authentication : Who are you ?

Authorization : You are an authenticated user, but what roles you have, what you are allowed to do?

JWT : Json Web Token. 



JWT Authentication Flow :

```cs
User Login
↓
Server Validates Credentials
↓
Server Generates JWT
↓
Client Stores JWT
↓
Client Sends JWT
↓
Server Validates JWT
↓
Request Allowed
```


---
>[!Note] how to implement `JWT` in ASP.NET

Configuring JWT `appsettings.json`

```cs
{
  "JwtSettings": {
    "SecretKey":
      "my-super-secret-key",
    "Issuer":
      "ProductApi",
    "Audience":
      "ProductApiUsers"
  }
}
```

Register JWT Authentication `Program.cs`

```cs
builder.Services.AddAuthentication(
    JwtBearerDefaults.AuthenticationScheme)
	.AddJwtBearer(options =>{
	});
```

add Authentication Middleware :
```cs
app.UseAuthentication();
app.UseAuthorization();
```

---
>[!NOTE] Role-Based Authorization

Suppose only ADMIN can delete products. So we use `[Authorize(Roles = "ADMIN")]`
If normal user/ customer tries to delete it we get : 403 Forbidden

```cs
[Authorize(Roles = "ADMIN")]
[HttpDelete("{id}")]
public IActionResult DeleteProduct(int id){
}
```

---
>[!NOTE] Policy-Based Authorization

```cs
[Authorize(Policy = "AdminOnly")]
```

register in `Program.cs`

```cs
builder.Services.AddAuthorization(options =>{
    options.AddPolicy("AdminOnly", policy => policy.RequireRole("ADMIN"));
    });
```

>[!QUEsTION] Wha is Refresh Token ?

Refresh tokens allow obtaining new access tokens without requiring the user to log in again.