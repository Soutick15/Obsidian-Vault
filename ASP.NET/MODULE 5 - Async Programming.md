
Async Programming in C# is similar concept like `CompletableFuture` , `thread pools`, and `asynchronous programming` in Java.

When client sends HTTPS request it goes from Controller -> service -> Database.

Now if the DB query takes 5 seconds to execute, the thread should not wait for its response. Instead of blocking the thread to do other work. 

async and await allow developers to write asynchronous code in a synchronous-looking style, improving readability and maintainability. We can use async programming to avoid blocking threads during I/O operations. 


Thread 1

Call Database
      ↓
Don't block
      ↓
Return thread to pool
      ↓
Continue later when result arrives

---

## `Task` 

`Task` represents an asynchronous operation that may complete in the future. 

`Task<T>` represents an asynchronous operation that returns a value. 





`Task` is Similar to `CompletableFuture<ProductResponse>` in java.

```cs
Task<User>
Task<string>
```

Java Comparison

```java
CompletableFuture<User>
```

### Async await Method example : 

```cs
public async Task<User> GetUser()
{
	//it will not wait for the result of  
    var user = await repository.GetUser();
    return user;
}
```


`async` keyword : The `async` keyword marks a method as asynchronous, it enables the use of await inside the method. async methods typically return `Task` or `Task<>`. 

`await` keyword :  The `await` keyword pauses the execution of a `async` method until the awaited task completes without blocking the current thread. This allows the application to remain responsive and efficiently utilize threads. Resumes execution when the task finishes.



Real ASP.NET Example

Controller :

```cs
public async Task<IActionResult> GetUser(int id){    
	var user = await _service.GetUser(id);    
	return Ok(user);
	}
```

Repository:

```cs
public async Task<User> GetUser(int id){    
	return await _context.Users.FindAsync(id);
	}
```

### Async vs Multithreading


Async : Thread is waiting.

Multithreading : multiple threads working in parallel.

---
### Thread vs Task


Thread : Thread is an actual execution unit provided by the operating system. Threads are Heavy & Expensive.

Task : It Represents asynchronous work. It is Lightweight and Managed by .NET runtime.

---
### Task.Run() : 
This actually uses a background thread. 

```cs
	var result = await Task.Run(() => {        
		return CalculateSomething();    
	});
```

Don't use Task.Run() for database calls.

Good:

```
await _context.Users.ToListAsync();
```

---

### What is CancellationToken?


> Production APIs often need cancellation. Suppose Client closes browser, then the Database should not continue processing. CancellationToken allows cooperative cancellation of asynchronous operations.

```cs
public async Task<List<User>>
GetUsers(CancellationToken token)
{
    return await _context.Users
                         .ToListAsync(token);
}
```

---

### Common Async Methods in ASP.NET

suffix + Async 


```cs
ToListAsync()
FindAsync()
FirstOrDefaultAsync()
SingleOrDefaultAsync()
SaveChangesAsync()
```


>[!question] If await doesn't block the thread, why does the next line execute later?

> await pauses the execution of the current method until the asynchronous operation completes. The method is suspended, but the underlying thread is not blocked and can be used for other work. When the operation completes, execution resumes from the point after await.