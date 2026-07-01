
01 Introduction & Fundamentals
│
├── What is JavaScript?
├── History of JavaScript
├── ECMAScript
├── JavaScript Versions
├── JavaScript Runtime
├── JavaScript Engine
├── Browser vs Node.js
├── How JavaScript Works
├── First JavaScript Program
├── Comments
├── Strict Mode
└── JavaScript Execution Flow
## What is JavaScript?

- JavaScript is a high-level, interpreted programming language developed by Brendan Eich in 1995 at Netscape for use in web browsers.
- It is widely known for making web pages dynamic and interactive by manipulating HTML and CSS.
- Initially it was designed for front-end development, though JavaScript is now used across the full stack, including back-end development with environments like Node.js.
- JavaScript is a single-threaded language, but it can handle asynchronous operations using mechanisms such as callbacks, promises, and async/await.
- Modern JavaScript engines, like Chrome’s V8, use Just-In-Time (JIT) compilation to boost performance.
- JavaScript is a multi-paradigm language, meaning it supports different styles of programming such as object-oriented, functional, and procedural programming. However, it is prototype-based, meaning it uses prototype-based inheritance rather than classical inheritance found in languages like Java or C++
- JavaScript is neither object-oriented programming language neither functional programming language it's a prototype based language.

## Interpreted programming language : 

An interpreted programming language is one where the source code is executed line by line by an interpreter at runtime. The interpreter translates the high-level code into machine code on the fly during execution. Examples include **JavaScript** and **Python**.

## Compiled language: 

In a compiled language, the entire source code is translated into machine code or lower-level intermediate code before execution. This process is handled by a compiler, which creates an executable file that can run directly on the machine. Examples include **C**, **C++**, and **Java**.

## JIT

Just-In-Time compilation is a technique used by modern Js engine to improve performance of JavaScript code. It combines the benefit of traditional interpreted execution and ahead of time(AOT) compilation by converting Js code on the go, just before its execution.

**Advantage of Interpreter:**
- Cross platform compatibility
- Easy to debug
- Rapid development

Disadvantage of Interpreter:
- Security concern because of visibility of source code
- Performances slower because of execution time.