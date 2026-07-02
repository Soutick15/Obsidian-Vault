
## Delegate : 

> Delegate is a object that can hold a reference to one or multiple methods that matches its specific signature and allows those methods to be invoked dynamically at runtime.
> 
> When we pass the delegate object in a program, it will call the referenced method.

### why we use Delegate ?

>Delegates allow us to pass methods as parameters, store methods in variables, implement callbacks, and support event-driven programming.
>
>Users can encapsulate the reference of a method in a delegate object.
>
>Lets create a custom event in a class - Suppose an order is placed(event) and we want to :

- **Send Email**
    
- **Send SMS**
    
- **Push Notification**
    
- **Write Audit Log**

### Creating a Delegate with `delegate` keyword : 

```cs
publics delegate void Notify();
```

This means : `Notify()` is a delegate that can store any method that matches its specific signature ie takes no parameters & returns void. 

One delegate can point to one or multiple methods. 

```cs
//Method 1
public static void SendEmail()
{
    Console.WriteLine("Email");
}

//method 2
public static void SendSms()
{
    Console.WriteLine("SMS");
}
```

```cs
	publics delegate void Notify();
	
	//Register the Method 1
	Notify notify = SendEmail;
	
	//Register the Method 2
	notify += SendSms;
	
	//Execute both SendEmail() & SendSms()
	notify();
```

```output
Email
SMS
```

---
>[!Example] Built-in Generic Delegates

Built-in generic delegates provided by .NET that cover the most common use cases, so we rarely need to create custom delegates today.

1.  `Predicate<>`
2. `Func<input, output>`
3. `Action<>`

### `Predicate<>` : 

Predicate is a built-in delegate that accepts one parameter and always returns a boolean value. 
It is is equivalent of `Predicate<T>` in Java. 

```javascript
Predicate<int> isEven = x => x % 2 == 0;
```

---
### `Func<>` delegate : 

- Func is a built-in generic delegate that represents a method which returns a value. 
- `Func<>` is equivalent of `Function<T,R>` in Java. 
- `Func<T,R>` : Takes input(s), returns a value. 
- `Func<int,int>` : takes one int input and returns one int value.
- `Func<int,int,int>`  : takes two int input and returns one int value.
- `Func<T>` : Takes no input, returns a value
- Last Generic type  represents the return Type.


```javascript

// takes one int input and returns one int value
Func<int,int> square = x => x * x;
Console.WriteLine(square(5)); //output : 25

//takes two int input and returns one int value.
Func<int,int,int> add = (a,b)=>a+b;

//Takes no input, returns a String value
Func<string> supplier = () => "Hello";
Console.WriteLine(supplier());

////Takes no input, returns a DateTime value
Func<DateTime> now = () => DateTime.Now;
```

---

### `Action<string>` Delegate :

- Action is a built-in delegate representing a method that does not return any value.
- `Action<string>` is equivalent of `Consumer<T>`

```cs
public static void Print(string name)
{
    Console.WriteLine(name);
}


Action<string> action = Print;
action("Soutick");

```

```javascript
Action<string> greet = name => Console.WriteLine(name);

greet("Soutick");
```

---
### Anonymous Methods

Anonymous methods allow us to define a method without giving it a name. In modern application almost everyone uses Lambda instead of Anonymous Method.

```javascript
delegate(int x)
{
    return x*x;
}
```

---
## Lambda Expressions

Lambda Expressions provide a short and readable syntax for writing anonymous functions.

```java
//Java Syntax
x -> x * x
```

```cs
// C# Syntax
x => x * x
```


Without lambda:

```cs
public static int Square(int x)
{
    return x * x;
}

Func<int,int> square = Square;
```

with lambda:

```cs

//Func<InputType, ReturnType>
Func<int,int> square = x => x * x;
```

---
### Events & EventHandler : 

> Events allow one object to notify other objects when something happens. They are built on delegates and follow the Publisher–Subscriber pattern.
Imagine : An order is placed(event) in Amazon and we want to :

- **Send Email**
    
- **Send SMS**
    
- **Push Notification**
    
- **Write Audit Log**

Amazon shouldn't manually call Email, SMS, Inventory, cause cause it will be tightly coupled.

Instead it publish a OrderPlaced Event making the services Loosely coupled. 