>[!info] Interface

Whenever we are declaring an interface we use `interface` keyword and prefix the interface name with capital `I`.

```cs
	public interface IPaymentService{
	    void ProcessPayment();
	}
	
	public interface IProductService{
	    void ProcessProduct();
	}
```

now if a class wants to implement this Interface we use `:` operator. 

```cs
public class ProductService : IProductService  {  

}
```

Java comparison

```java
@Service
public class ProductServiceImpl implements ProductService {

}
```
---

>[!info] Abstract class

The declaration of an abstract method is very similar to Java. We use `abstract` keyword before the class and method name. 

```cs
public abstract class Animal {
	public abstract void Sound();
}
```

```cs
//Inheritence : `Dog` is implementing `Animal`
public class Dog : Animal {

// using `override` implementating the Parent class method
    public override void Sound(){
        Console.WriteLine("Bark");
    }
}
```

---

>[!question]   What is the difference between an abstract class and an interface?

Interface Represents : Capability. 
An interface defines a contract that specifies what a class must do, but not how it does it.

``` c#
IFlyable
ISwimmable
IPaymentService
```

Abstract Class Represents : Common Base Behavior. 
An abstract class is used to provide a common base class with shared implementation and common state.

```CS
Animal
Vehicle
Employee
```

|Abstract Class|Interface|
|---|---|
|Used to declare properties, events, methods, and fields as well.|Fields cannot be declared using interfaces.|
|Provides the partial implementation of functionalities that must be implemented by inheriting classes.|Used to declare the behavior of an implementing class.|
|Different kinds of access modifiers like private, public, protected, etc. are supported.|Only public access modifier is supported.|
|It can contain static members.|It does not contain static members.|
|Multiple inheritances cannot be achieved.|Multiple inheritances are achieved.|


---
>[!info] Topic 3: Virtual and Override

>In Java by default child class methods can override parent class methods. 
>
>But in `C#` parent class methods are not overridable by default. We need to mark parent method with `virtual` so that child class can provide a different implementation. 

>`virtual` : Marks a method in the parent class as overridable.
>`override` : using `override` keyword child class method can provides a new implementation of the parent class method.

```cs
//parent
public class Animal
{
    public virtual void Sound()
    {
        Console.WriteLine("Animal");
    }
}
//child
public class Dog : Animal
{
    public override void Sound()
    {
        Console.WriteLine("Dog");
    }
}
```

---
>[!info] Sealed Classes

A **sealed class** is a class that is used to control inheritance, You can **restrict** which classes are allowed to extend or implement your class.

It provides ; Security, Performance and Prevent misuse.

```CS
public sealed class JwtTokenGenerator
{
}
```

>[!info] Static Class

Without creating object we can directly access the class properties.

In `Java` we usually do :

```Java
public class MathUtil {

    public static int Add(int a, int b) {
        return a + b;
    }
}

public class Test{
	public static void main(String[] args){
		int result = MathUtil.add(10, 20);
	}
}
```

in `C#` we do : 

```cs
public static class MathUtil
{
    public static int Add(int a, int b)
    {
        return a + b;
    }
}

MathUtil.Add(10,20);

//Compile Time Error : Can't create Object of a `static` class
new MathUtil(); 
```


>[!info] Struct vs Class

| Class                                                                                     | Struct                                                                  |
| ----------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| Reference Type                                                                            | Value Type                                                              |
| stored on Heap area                                                                       | Value Semantics                                                         |
| Supports Inheritance                                                                      | Doesn't support class inheritance                                       |
| Used Most Often for Entities, Services, Controllers, Repositories, DTOs (usually records) | used for Small immutable values, Coordinate, Money, Date-related values |
class :

``` cs
public class Employee
{
    public string Name { get; set; }
}

	Employee e1 = new Employee();

	// copy the object rference to e2
	Employee e2 = e1; 
	
	//Now both e2 and e1 is holding the same object reference
```

Struct

```cs
public struct Point
{
    public int X { get; set; }
    public int Y { get; set; }
}
	Point p1 = new Point();
	
	//Complete copy created.
	Point p2 = p1; 
```