Functions

Function Declaration

Function Expression

Anonymous Functions

Named Function Expression

Arrow Functions

IIFE

Callback Functions

Higher Order Functions

Pure Functions

Recursive Functions

Generator Functions

Async Functions

Default Parameters

Rest Parameters

Spread Parameters

arguments Object

Function Scope

Lexical Scope

Scope Chain

Closures

Execution Context

Call Stack

Hoisting

this Keyword

bind()

call()

apply()

Currying

Partial Application

Memoization

Function Composition

Best Practices

Interview Questions

Real Project Examples

# **Function**

A function is a reusable block/series of code that perform a specific task or set up tasks when you call the function.

It promotes code reusability, and readability.

**Function output and return value**
- `return` keyword stop the execution and return the cursor of the execution to its caller method.
- only single value will be returned and it can return any type of value because of it’s dynamic type.
- When the function is not returning any value writing `return` is optional, by default the written type is undefined.
- Anything written after return keyword doesn't execute.
- A function which is attached with an object is known as method. Ex-Math.floor().

**Creating a function:** use `function` keyword

```javascript
function function_name(){
	//instructions
	return value;
}

//calling the function and store the returned value
var store = function_name();

```


**Two types of parameters are there in functions:**

1. Parameter (during declaration)

2. Arguments (during calling)

```javascript
function m1(a, b){
	return a + b;
}

m1(10,10); //20
```


**Calling a function with arguments:**

In JavaScript, while calling a function you can pass **any type of value** : number, string, object, array etc.

You can call a function with: with less number of arguments, equal number of arguments or more number of arguments.

If we call with zero or less number of arguments, the default value “undefined” will be assigned to it’s parameters.

If we call with more number of arguments, it will ignore the extra/unwanted arguments.

```JavaScript
function m1(a, b) {
	console.log(a, b);
}

// A = 10 and B = 10
m1(10,10); 

 // A = 10 and B = jsp
m1(10,"jsp");

// A = 10 and B is undefined
m1(10);

// A is undefined and B is undefined
m1();

 // A = 10 and B = 20 and 30 is ignored
m1(10,20,30);
```


---
## **Difference between Expression and statement**

**Expressions:** An **expression** is any valid unit of code that can be evaluated and will return a value. It can be as simple as a single variable, or more complex, involving operators and function calls.

```Javascript
5 // A number literal, value → 5

"Hello" // A string literal, value → "Hello"

x // value → whatever x holds

x + 5 // An arithmetic expression

Math.max(5, 10) // An expression that returns 10

let x = 10; //10 → expression, x = 10 → assignment expression (returns 10)
```

**Statements:** A **statement** is a complete instruction that performs an action but do not return a value. Instead, they are executed to change the state of the program.

Statements can include expressions, but they can also stand alone as commands.

```Javascript
let y = 5; // Statement that declares a variable y and assigns it a value

if (y > 3) {// An if statement that executes a block of code

console.log("y is greater than 3");

}

function greet() { // A function declaration is a statement
	console.log("Hello!");
}

return x; // A return statement that exits a function and returns a value
```

---

## **Function Expression**

A nameless function , which is stored inside of a variable. It behaves just like a normal function. The `function` keyword can be used to define a function  inside of an expression.


```javascript
let sum = function(a, b) {
	return a+b;
}

console.log(sum); //prints the whole function, does not execute it
console.log(sum(5,6)); //calling the function
```

You can call the function with the variable which has stored the function followed by `()`. 

If we call the function name without parenthesis `()`, the whole function will be printed, rather than executing it.


---
### **Function declaration / statement** vs **Function expression**


|               Function declaration / statement                |                                    **Function expression**                                     |
| :-----------------------------------------------------------: | :--------------------------------------------------------------------------------------------: |
| Function declaration/statement can be called before creation. | Function expression cannot be called before creation, because the variable is not declared yet |
|              It's a block of code ends with `}`               |                               It is a statement ends with a `;`                                |


---

## **Self-calling Function / Immediately Invoked Function Expression (IIFE):**

A **self-calling function or IIFE** in JavaScript is a function that executes immediately after it is defined.

The primary use of it is to create a new scope, ensuring that variables inside the function don’t interfere with other parts of your code.

**Why Use IIFE?**

Variables declared inside an IIFE are not accessible from the outside, which prevents polluting the global scope.

You can use IIFE to create private variables, making it a common pattern in JavaScript for module creation.

It helps isolate code blocks and protects them from unintended interactions with other parts of the program.

```Javascript
(function() { console.log("I am a self-calling function!");})();
```

---
### **Pure Function & Impure Function:**

**Pure Function:**

A pure function does NOT change any value outside and it always gives the same output for same input.

Pure function has n**o Side Effects, means** it does not modify global variables, does not change external data, does not do API calls / DB updates.

```javascript
function add(a, b) {
	return a + b;
}
```

**Impure Function:**

An impure function modifies external states or variables, meaning it can affect other parts of the program beyond its own scope.

**It has side effects :** Given the same inputs, an impure function might return different outputs, as its behaviour could depend on external factors like global variables, random values, or modifying external states.

```javascript
let total = 0;

function impureAdd(a, b) {
	total = a + b;
	return total; //The output depends on and affects an external state

}
```

---

## First-Class Functions (First-Class Citizens)


In JavaScript, **functions are first-class citizens**, meaning they are treated just like normal value (such as numbers or strings). They can be 
1. Assigned to variables, 
2. passed as arguments to another function
3. Returned as a value from other functions
4. Stored in data structures like arrays or objects
---

### 1. Assigning a Function to a Variable

```javascript
const greet = function () {
    console.log("Hello!");
};

greet(); // Hello
```
---

### 2. Passing a Function as an Argument

```javascript
function execute(callback) {
    callback();
}

function greet() {
    console.log("Hello!");
}

execute(greet);
```

### Real Project Example

```javascript
function fetchData(onSuccess) {
    // Fetch data from API...
    onSuccess();
}

fetchData(() => {
    console.log("Products loaded successfully.");
});
```

This pattern is commonly used in **callbacks**, **event handlers**, and **array methods** like `map()`, `filter()`, and `forEach()`.

---

## 3. Returning a Function from Another Function

```javascript
function outer() {
    return function () {
        console.log("Inside returned function");
    };
}

const result = outer();
result();
```

This concept is the foundation of **Closures** and **Higher-Order Functions**.

---

## 4. Storing Functions in Arrays and Objects

### Array

```javascript
const actions = [
    () => console.log("Login"),
    () => console.log("Logout")
];

actions[0]();
```

### Object

```javascript
const user = {
    name: "Soutick",
    age: "24",
    login() {
        console.log(`${this.name} logged in`);
    }
};

user.login();
```


---

## Where Are First-Class Functions Used?

- Event Listeners
- Callback Functions
- Promises
- Async/Await
- Array Methods (`map`, `filter`, `reduce`, `forEach`)
- Closures
- Higher-Order Functions
- React Event Handling
- Express.js Middleware

---

## A **higher-order function (HOF)** :

This is a function that either takes one or more functions as arguments (callbacks), or Returns a function as its result.

So later, that function gets called back (executed) inside the outer function.

The functions which are passed as an argument to high-order function are called callback function.

```Javascript
function greet(name) {
	return `Hello, ${name}!`;
}

function processUserInput(callback) {
	const name = prompt("Please enter your name.");
	console.log(callback(name));
}

processUserInput(greet); // Passing the greet function as an argument
```

```Javascript
function multiplier(factor) {
	return function(number) {
		return number * factor;
	};
}

const double = multiplier(2);
console.log(double(5)); // Output: 10
```

```javascript
document.getElementById('myButton').addEventListener(
	'click', function(){
		alert('Button clicked!');
	}
);
```

---
## **Anonymous functions**

A **Anonymous functions** have no name and are used mostly for temporary or one-off tasks. 

They are commonly used in callbacks, event handlers, and array methods.

**Arrow functions** offer a concise way to write anonymous functions, especially for shorter, simpler tasks.

```javascript
setTimeout(function() {
	console.log("This is an anonymous function!");
	}, 2000
); // This function will run after 2 seconds
```

```Javascript
const greet = () => {
	console.log("Hello!");
};

greet(); // Output: Hello!
```

```javascript

document.getElementById('myButton').addEventListener('click', function() {
	alert('Button clicked!');
});
```

---
## **Arrow Function**

Introduced in ES6-ECMAScript 2015

Arrow functions are a modern feature of JavaScript that simplifies function syntax and helps avoid common difficulties with “this” binding.

Do not have their own “this” context they inherit “this” from the surrounding lexical context.

Arrow functions cannot be used as constructors and will throw an error if you try to use them with the new keyword.

```Javascript
const add = (a, b) => {
	return a + b;
};
```

✦ If the function body contains only a single expression, you can omit the curly braces {} and the return

keyword: **(param1, param2, ..., paramN)** **=>** **expression**

✦ If the arrow function has no parameters, you use empty parentheses: **()** **=>** **{ statements }**

✦ For a single parameter, you can omit the parentheses: **param** **=>** **{ statements }**


---
## **what is function currying**

Function currying is a technique where a function that takes multiple arguments is converted into a chain of functions, where each function take a single argument at a time and returns another function until all arguments are provided.

Each function returns another function that takes the next argument, until the final function returns the result.

It helps in creating more specialised functions by partially applying arguments.

**Benefits** include improved reusability, easier function composition, and flexible partial application of arguments.

So instead of doing : function add(a, b, c){ return a + b + c; }

```javascript
function curriedAdd(a) {
	return function(b) {
		return function(c) {
			return a + b + c;
		};
	};
}


const add5 = curriedAdd(5); // Returns a function that adds 5
const add5And3 = add5(3); // Returns a function that adds 5 and 3
console.log(add5And3(2)); // Output: 10
```

1. curriedAdd(5) returns a function that adds 5 to its argument.
2. .add5(3) returns a function that adds 3 to the previous result.
3. .add5And3(2) completes the calculation by adding 2 to the result.


