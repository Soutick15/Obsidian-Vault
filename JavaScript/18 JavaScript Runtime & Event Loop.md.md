JavaScript Runtime

Execution Context

Call Stack

Memory Heap

Event Loop

Task Queue

Microtask Queue

Macrotask Queue

Rendering Pipeline

Browser Rendering

Node.js Event Loop

Event Loop Internals

Interview Questions


# JavaScript Runtime Environment


A **JavaScript Runtime Environment** provides necessary infrastructure for JavaScript to execute JavaScript code. 

It includes the JavaScript Engine and additional components that enable JavaScript to interact with the browser or server.

---

## Components of JavaScript Runtime Environment

| Component | Purpose |
|----------|---------|
| **JavaScript Engine** | Parses, compiles, and executes JavaScript code (e.g., Google's **V8 Engine**). |
| **Call Stack** | Executes function calls in a Last-In-First-Out (LIFO) order. |
| **Heap Memory** | Stores objects, arrays, and dynamically allocated data. |
| **Web APIs / Node.js APIs** | Provide browser or server functionalities like `setTimeout()`, `fetch()`, DOM, File System, etc. |
| **Callback Queue** | Holds completed asynchronous callbacks waiting to be executed. |
| **Event Loop** | Continuously checks whether the Call Stack is empty and moves callbacks from the Callback Queue to the Call Stack. |

---

![[Pasted image 20260628181942.png]]

---

## Execution Flow

1. JavaScript code is executed by the **JavaScript Engine**.
2. Function calls are pushed onto the **Call Stack**.
3. Objects and arrays are stored in **Heap Memory**.
4. Asynchronous operations (e.g., `setTimeout()`, `fetch()`) are delegated to **Web APIs**.
5. Once completed, their callbacks are placed in the **Callback Queue**.
6. The **Event Loop** waits until the Call Stack is empty, then moves callbacks from the Callback Queue to the Call Stack for execution.

---

## Real Project Example

```javascript
console.log("Start");

setTimeout(() => {
    console.log("Payment Successful");
}, 2000);

console.log("Processing...");
```

### Execution Flow

```text
Call Stack
-----------
console.log("Start")
↓

Web API
--------
setTimeout(2s)

↓

console.log("Processing")

↓

Callback Queue
--------------
console.log("Payment Successful")

↓

Event Loop

↓

Call Stack

↓

Payment Successful
```

### Output

```text
Start
Processing...
Payment Successful
```

---

## Browser vs Node.js Runtime

| Browser Runtime | Node.js Runtime |
|-----------------|-----------------|
| DOM APIs | File System (`fs`) |
| `fetch()` | Process API |
| `localStorage` | Buffer |
| `setTimeout()` | `setTimeout()` |
| WebSocket | HTTP Module |

---

> [!TIP]
> The **JavaScript Engine** is responsible only for executing JavaScript code. Features like **DOM manipulation**, **`fetch()`**, **`setTimeout()`**, and **File System access** are provided by the **runtime environment**, not by JavaScript itself.

---

## Interview Questions

### Is `setTimeout()` part of JavaScript?

**No.** It is provided by the browser's Web APIs (or Node.js runtime), not by the JavaScript language itself.

---

### Why can JavaScript perform asynchronous operations if it is single-threaded?

Because the runtime environment delegates asynchronous tasks to **Web APIs/Node.js APIs**, while the **Event Loop** ensures callbacks are executed when the Call Stack becomes empty.

---

### Does the JavaScript Engine contain the Event Loop?

No. The **Event Loop** is part of the **runtime environment**, not the JavaScript Engine itself.