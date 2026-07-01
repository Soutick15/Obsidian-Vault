Errors

Syntax Error

Reference Error

Type Error

Range Error

URI Error

try

catch

finally

throw

Custom Errors

Error Object

Stack Trace

Debugger

Console API

Source Maps

Best Practices

Interview Questions


# Console

The **`console`** object provides access to the browser's debugging console. It is mainly used to **log information, debug applications, measure performance, and inspect data** during development.

---

## Common Console Methods

| Method with Example                                   | Purpose                                                                      |
| ----------------------------------------------------- | ---------------------------------------------------------------------------- |
| `console.log(user);`                                  | Prints general messages or variable values.                                  |
| `console.warn("Low disk space");`                     | Displays a warning message.                                                  |
| `console.error("API request failed");`                | Displays an error message.                                                   |
| `console.info("Server started");`                     | Displays informational messages.                                             |
| `console.debug(response);`                            | Prints debug information (may be hidden unless DevTools is in verbose mode). |
| `console.table(users);`                               | Displays arrays or objects in a table format.                                |
| `console.group("User Details");`                      | Groups related logs together.                                                |
| `console.time("API");`                                | Measures execution time of a block of code.                                  |
| `console.assert(age >= 18, "User must be an adult");` | Logs a message only if the condition is **false**.                           |
| `console.clear();`                                    | Clears the console.                                                          |
| `console.count("Click");`                             | Counts how many times a label has been logged.                               |
| `console.countReset("Click");`                        | Resets the counter for a label.                                              |
| `console.trace();`                                    | Prints the current function call stack.                                      |
| `console.dir(user);`                                  | Displays an interactive list of an object's properties.                      |

---

## Real Project Examples

### Logging API Response

```javascript
fetch("/api/products")
    .then(response => response.json())
    .then(data => {
        console.log(data);
    });
```

---

### Displaying Data as a Table

```javascript
const employees = [
    { id: 1, name: "John", department: "IT" },
    { id: 2, name: "Jane", department: "HR" }
];

console.table(employees);
```

---

### Measuring API Execution Time

```javascript
console.time("Fetch Products");

await fetch("/api/products");

console.timeEnd("Fetch Products");
```

---

### Grouping Related Logs

```javascript
console.group("User Login");

console.log("Username: soutick");
console.log("Role: Admin");
console.log("Status: Success");

console.groupEnd();
```

---

### Checking Conditions

```javascript
const age = 16;

console.assert(age >= 18, "User must be at least 18 years old");
```

---

> [!TIP]
> Remove or minimize unnecessary `console.log()` statements before deploying to production. They can clutter logs and may expose sensitive information.