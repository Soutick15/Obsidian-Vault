Variables

var

let

const

Variable Scope

Variable Shadowing

Hoisting

Temporal Dead Zone

Primitive Data Types

Reference Data Types

typeof Operator

Type Conversion

Implicit Conversion

Explicit Conversion

Type Coercion

Truthy Values

Falsy Values

null

undefined

NaN

Infinity

BigInt

Symbol

== vs ===

Object.is()

Best Practices

Interview Questions

# JavaScript Data Types & Variables

> [!NOTE]
> **Data Types** define the kind of value a variable can store. Since JavaScript is a **dynamically typed language**, a variable can hold different types of values during program execution.

---

# JavaScript Data Types

JavaScript has **8 built-in data types**.

| Data Type | Description | Example |
|------------|-------------|---------|
| **String** | Sequence of characters enclosed in quotes | `"Hello"`, `'JavaScript'`, `"123"` |
| **Number** | Integer or floating-point numbers | `10`, `-5`, `3.14` |
| **Boolean** | Logical values | `true`, `false` |
| **Undefined** | Variable declared but not assigned a value | `let age;` |
| **Null** | Intentional absence of a value | `let user = null;` |
| **BigInt** | Stores integers larger than the Number limit | `12345678901234567890n` |
| **Symbol** | Creates unique identifiers | `Symbol("id")` |
| **Object** | Collection of key-value pairs | `{name: "John"}` |

> [!IMPORTANT]
> Except **Object**, all other JavaScript data types are **Primitive Data Types**.

---

 1. String : A **String** is a sequence of characters enclosed within single quotes (`' '`), double quotes (`" "`), or backticks (`` ` ` ``).
  
```javascript  
const customerName = "Soutick";  
const customerCity = 'Bangalore';  
const orderStatus = "Delivered";  
const otp = "123456"; // Numbers stored as text  
const welcomeMessage = `Welcome ${customerName}`;  
```

---

 2. Number : JavaScript has only **one Number type**. 

```javascript
let age = 25;
let price = 499.99;
let temperature = -10;

console.log(typeof price); // number
```

---

3. Boolean : Boolean stores only **two values**: `true` or `false`

```javascript
let isLoggedIn = true;
let isAdmin = false;

if (isLoggedIn) {
    console.log("Show Dashboard");
} else {
    console.log("Redirect to Login");
}
```

---

4. Undefined : A variable is **undefined** when it has been declared but **not assigned any value**. `undefined` is automatically assigned by JavaScript. It is **not an empty value**—it means "value not assigned yet."

```javascript
let salary;

console.log(salary);          // undefined
console.log(typeof salary);   // undefined


let selectedProduct;

console.log(selectedProduct);
// User hasn't selected any product yet.
```

---

5. Null : `null` represents the **intentional absence of a value**. The programmer explicitly assigns `null` when they want to indicate "no value."

```javascript
let manager = null;

console.log(manager);
```

> [!WARNING] 

> Due to a historical JavaScript bug: Although `null` is **not an object**, JavaScript still returns `"object"` for historical compatibility.

```javascript
console.log(typeof null); // object
```


---

### Undefined vs Null

| Undefined                                                                            | Null                                             |
| ------------------------------------------------------------------------------------ | ------------------------------------------------ |
| `undefined` means a variable is declared, but has not been assigned any value        | `null` is explicitly assigned by the programmer. |
| `undefined` is typically used to indicate that something is un-initialised or absent | It represents intentional absence of a value.    |
| `typeof` returns `"undefined"`                                                       | `typeof` returns `"object"` (legacy bug)         |

Example

```javascript
let a;
let b = null;

console.log(a); // undefined
console.log(b); // null
```
---

### **`undefined` vs `not defined`**
**undefined:** Indicates that a variable has been declared but not assigned a value, or that a property or element does not exist. **undefined** is a **value** in JavaScript.

**`Not Defined`:** It is an error message that occurs when you’re trying to access a variable that was never declared.

```javascript
//example 1
let x;
console.log(x); // undefined

//example 2
function test(a) {
	console.log(a);
}

test(); // undefined

console.log(x); // ReferenceError: x is not defined
```

---

6. BigInt : `BigInt` is used to store integers larger than the safe limit of the `Number` type. The maximum safe integer for `Number` is:

```javascript
Number.MAX_SAFE_INTEGER //9007199254740991
```


Numbers larger than this may lose precision.

### Creating BigInt

Using `n`

```javascript
const id = 123456789012345678901234567890n;
```

Using `BigInt()`

```javascript
const value = BigInt("123456789012345678901234567890");
```

### Real Project Example

Large financial systems or banking applications may use BigInt for very large transaction IDs.

---

7. Symbol : A `Symbol` creates a **unique and immutable value**. Even if two Symbols have the same description, they are **never equal**.

```javascript
const id1 = Symbol("id");
const id2 = Symbol("id");

console.log(id1 === id2); // false
```


---

8. Object : Objects store data as **key-value pairs**.

```javascript
const employee = {
    id: 101,
    name: "Soutick",
    salary: 80000
};
```

---

 JavaScript is Dynamically Typed. Unlike Java or C, JavaScript variables **do not have fixed data types**. The same variable can store different kinds of values.


```javascript
let value = 100;

value = "JavaScript";

value = true;

console.log(value); // true
```

> The variable changes from **Number → String → Boolean** without any error.

---

 NaN (Not-a-Number) : `NaN` stands for **Not-a-Number**. It represents an invalid numeric result.


```javascript
console.log(0 / 0); // NaN

console.log(Number("Hello")); // NaN

console.log(Math.sqrt(-1)); // NaN
```

---

# Interesting Facts about NaN

 `typeof NaN` : Although it means "Not-a-Number," its type is still `"number"`.

```javascript
console.log(typeof NaN); //number
```

---

### NaN is never equal to itself

```javascript
console.log(NaN === NaN); // false
```

---

### Checking NaN

```javascript
console.log(Number.isNaN(NaN));     // true
console.log(Number.isNaN(100));     // false
console.log(Number.isNaN("Hello")); // false
```

> [!TIP]
> Prefer `Number.isNaN()` over the global `isNaN()` because it avoids unwanted type coercion.

---

# Variable Declaration

JavaScript provides **three ways** to declare variables.

```javascript
var name = "John";

let age = 25;

const country = "India";
```

---

# difference between `var` vs `let` vs `const`

| var                                                                         | let                                                                                                  | const                                                                                                              |
| --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| The scope of a var variables are functional or global scope.                | The scope of let variables are block scope                                                           | The scope of const variables are block scope                                                                       |
| Var can be declared without initialisation.                                 | Let can be declared without any initialisation.                                                      | Const can’t be declared without any initialisation.                                                                |
| Var can be accessed without initialisation as default values is “undefined” | Let can’t be accessed without initialisation, it gave “referenceError”.                              | Const cannot be accessed without initialisation, as it cannot be declared without initialisation.                  |
| Var variables are hoisted.                                                  | Let variables are also hoisted, but they stays in the “Temporal dead zone” until the initialisation. | const variables are also hoisted, but same as let they stays in the “temporal dead zone” until the initialisation. |
| Var can be re-initialised and re-declared in the same scope                 | Var can be re-initialised, but can not be re-declared in the same scope                              | Var can neither be re-initialised, nor re-declared.                                                                |
|                                                                             |                                                                                                      |                                                                                                                    |

---


# Checking Data Type

Use the `typeof` operator to determine the type of a value.

### Syntax

```javascript
typeof value;
```

### Example

```javascript
let name = "John";
let age = 25;
let isAdmin = true;

console.log(typeof name);
console.log(typeof age);
console.log(typeof isAdmin);
```

Output

```text
string
number
boolean
```

---

# Variable Scope

Variable scope determines **where a variable can be accessed**.

## 1. Local Variable

A local variable is declared **inside a function or block** and is only accessible within that scope.

### Example

```javascript
function greet() {
    let message = "Hello";
    console.log(message);
}

greet();
// console.log(message); // Error
```

### Real Project Example

```javascript
function calculateTotal(price, tax) {
    let total = price + tax;
    return total;
}
```

The `total` variable is available only within the function.

---

## 2. Global Variable

A global variable is declared **outside all functions and blocks**, making it accessible throughout the program.

### Example

```javascript
let appName = "Shopping App";

function displayApp() {
    console.log(appName);
}

displayApp();

console.log(appName);
```

### Real Project Example

```javascript
const API_BASE_URL = "https://api.example.com";
```

This constant can be reused across different modules for making API requests.

> [!WARNING]
> Excessive use of global variables can lead to unexpected bugs and naming conflicts. Prefer local variables and modular code when possible.

---

# Best Practices

- ✅ Use `const` whenever possible.
- ✅ Use `let` only when reassignment is required.
- ✅ Avoid `var` in modern JavaScript.
- ✅ Use meaningful variable names.
- ✅ Prefer `Number.isNaN()` for checking `NaN`.
- ✅ Use `null` intentionally to represent "no value."
- ✅ Minimize the use of global variables to reduce side effects.

---

# Common Interview Questions

### Why is JavaScript called a dynamically typed language?

Because a variable's data type is determined at runtime and can change without redeclaration.

---

### What is the difference between `undefined` and `null`?

- `undefined` means a variable has been declared but not assigned a value.
- `null` is an explicit assignment indicating the intentional absence of a value.

---

### Why does `typeof null` return `"object"`?

This is a long-standing historical bug in JavaScript that has been preserved for backward compatibility.

---

### What is `NaN`?

`NaN` stands for **Not-a-Number** and represents an invalid numeric result. Although its name suggests otherwise, `typeof NaN` returns `"number"`.

---

### Why are Symbols useful?

Symbols create unique identifiers, making them ideal for object property keys that should not conflict with other properties.

---


## Hoisting in JavaScript

Hoisting is a JavaScript mechanism where variables and function declarations are moved to the top of their current scope before code execution.

This means that you can use variables and function even before they are actually declared in the code.

In Global execution context JavaScript allocates memory to all variables and functions even before any line of code start executing.

However, only the declarations are hoisted, not the initialisations.

1.  **Variable (Var) Hoisting :**

- Variables declared with “var” are hoisted to the top of their function or global scope.
- Only the declaration is hoisted, not the initialisation.
- You get “undefined” if you try to access the variable.
- JavaScript allocates memory space, and put a placeholder “undefined”.

```javascript
console.log(myVar);//undefined

var myVar = 10;

console.log(myVar);//10
```

![[Hoisting.excalidraw]]

2. **Function Hoisting:**

- Function declarations are fully hoisted with their full definitions.
- Both declarations and initialisations are moved to the top of their scope.
- It allows to can call the function before its declaration in the code.


```javascript
sayHello(); //Hello

function sayHello(){
	console.log("Hello");
}

sayHello(); //Hello

```

However, function expressions and arrow functions are not hoisted in the same way.

```javascript
greet(); // TypeError: greet is not a function

var greet = function() {
	console.log("Hello, World!");
};
```


3. **Let and Const Hoisting:**

- Variables declared with let and const are hoisted but are in a “temporal dead zone” until their declaration is encountered.
- Accessing them before their declaration result in a “ReferenceError".

```javascript
console.log(myLet); // ReferenceError: Cannot access before initialisation
let myLet = 10;

console.log(myConst); // ReferenceError: Cannot access before initialisation
const myConst = 10;
```

- During JavaScript execution, both let and const variables are allocated memory in their respective execution contexts (block scope) when the code is compiled.
- However, they do not get added to the global object (window).
- Instead, they stay in a different memory space (the block scope) that is not accessible until they are declared.
- Since they are not in global Object(window object), accessing them cause “Temporal dead zone”
----
## Block (Compound Statement)

A **Block** (also called a **Compound Statement**) is a code structure used to group statements together within curly braces `{}`.

Blocks allow us to execute **multiple statements** where JavaScript expects only a **single statement**.

Without a block, an `if` statement can execute only **one statement**.

```javascript
if (age >= 18)
    console.log("Adult");
    console.log("Can drive"); 
    console.log("Can drink");
```

If we want to execute multiple statements, we must group them inside a block.

```javascript
if (age >= 18) {
    console.log("Welcome");
    console.log("Can drive");
    console.log("Can drink");
}
```

---

### Block Scope

Variables declared using **`let`** and **`const`** are **block-scoped**, meaning they are accessible **only inside the block** where they are declared.

`var` is **not block-scoped**. It is **function-scoped** (or globally scoped if declared outside a function).

```javascript
{
    let username = "Soutick";
    const role = "Admin";

    console.log(username); // Soutick
    console.log(role);     // Admin
}

console.log(username); // ReferenceError
console.log(role);     // ReferenceError
```

---

### Nested Blocks

A block can contain another block. Each nested block creates its own scope.

```javascript
{
    let outer = "Outer";

    {
        let inner = "Inner";

        console.log(outer); // Outer
        console.log(inner); // Inner
    }

    console.log(outer); // Outer
    console.log(inner); // ReferenceError
}
```

---
## **Truthy & Falsy**

Everything is true or false (boolean) in JavaScript

**False Values:** 
```Javascript
false 
0 
-0 
0n 
" "
null
undefined, 
NaN
```

**Truthy Values:** Truthy values are all values that are not falsy. In other words, everything else in JavaScript is considered true when evaluated in a boolean context.
