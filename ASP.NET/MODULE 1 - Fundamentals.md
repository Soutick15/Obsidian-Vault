data types in C# :

```cs
	string name = "Soutick";
	string? name; // name can be null. (null is allowed)
	int age = 25;
	bool isAdult = true;
	double phone = 8637363701;
	var name = "John"; //dynamically determines the type. Implies 'string' at compile time
```

var :  var is not dynamic . var is resolved at compile time.  The type is still strongly typed. if we try to do like this below we will get error.

```c#
var name = "John";
name = 10; //error 
```

defining a class :

```cs
	public class Employee {
	
	public string Name { get; set; }
	
	//constructor
	public Employee(string name){
	    Name = name; // notice we write `Name` instead of `this.name`
    }    
}
```


```cs
	public class Employee {
	
	//Only getter, for read-Only Property
	public string Name { get; } 
	
	 //Private Setter
	public string Name { get; private set; }
}
```

