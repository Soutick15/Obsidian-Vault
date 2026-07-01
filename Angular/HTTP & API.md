>[!question]  How do you make HTTP calls?

HTTP calls in Angular are mainly made using the `HttpClient` service provided by `HttpClientModule`

First, import & register the `provideHttpClient`  in `app.config.ts`.

```typescript

// `app.config.ts`
import { provideHttpClient } from '@angular/common/http';

export const appConfig = {
  providers: [
    provideHttpClient()
  ]
};
```

In real-world applications, HTTP calls are usually written inside Services. So, inside service component we need to import and inject `HttpClient`

`HttpClient` is used to communicate with backend APIs using operations such as: GET, POST, PUT, DELETE

```typescript
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class ProductService {

  constructor(private http: HttpClient) {}

  getProducts() {
    return this.http.get<any[]>(
      'http://127.0.0.1:8080/api/v1/products'
    ).subscribe(data => {
    console.log(data);
  });
  }

}
```



Observables : Angular HTTP calls are asynchronous and return **RxJS Observables** - (An **Observable** is a stream of data).

HTTP Observables are lazy. The request is not sent until someone subscribes to it.

### Flow

```text
Component
    ↓
ProductService
    ↓
HttpClient
    ↓
Backend API
```

>[!question] **15. What are Interceptors?** 

- Interceptors in Angular are used to intercept and modify HTTP requests and responses globally before they are sent to the backend or received by the application.
- **They are commonly used for:**

- adding JWT tokens
- authentication
- logging
- error handling
- request/response modification 

## **RxJS** 


> [!question]  What is RxJS (Reactive Extensions for JavaScript)?

RxJS stands for **Reactive Extensions for JavaScript**.

It is a library used in Angular for handling **asynchronous operations**, **data streams**, and **reactive programming**.

RxJS mainly works with **Observables** and **Operators**. 

Angular heavily uses RxJS for:
    
    - HTTP Calls
        
    - Event Handling
        
    - Form Value Changes
        
    - Search/Autocomplete
        
    - WebSockets
        
    - State Management
        

---

`Observable` : An Observable represents a stream of future values over time. Unlike normal values, an Observable does not execute until someone subscribes to it.

```typescript
// The Observable is what `this.http.get()` returns.
this.http.get('/users')
  .subscribe(data => {
    console.log(data);
  });
```

---

`Operators` : Operators are functions used to transform, filter, combine, or manipulate Observable data. 

Examples:

- `map()`
- `filter()`
- `switchMap()`
- `debounceTime()`

```typescript
search$
  .pipe(
    debounceTime(300)
  )
  .subscribe();
```

---

>[!question]  **17. Observable vs Promise**

Both Observable and Promise are used for handling asynchronous operations in Angular, but they work differently.

>[!info] Promise

```javascript
fetch('/users')
  .then(data => console.log(data));
```
- A Promise returns only one single future value.
- Promise Executes immediately and Cannot be cancelled easily. 
- Promise is mainly used for One-time async operations & Simple JavaScript tasks

---

>[!info]  Observable

```typescript
this.http.get('/users')
  .subscribe(data => console.log(data));
```

- An Observable represents a stream of future values. Means Can return multiple values over time.
- Observable Executes only after calling `subscribe()` & Can be cancelled using `unsubscribe()`
- Supports RxJS operators
- Observable are used for
- HTTP calls
- Form value changes
- Search/autocomplete
- WebSockets
- Event streams

> [!question]  18 How do you Unsubscribe? -  why we want to unsubscribe?

Observables can continue emitting values even after a component is destroyed. If we don't unsubscribe, the subscription may continue running in the background, leading to memory leaks and unnecessary resource usage.

Angular provides multiple ways to unsubscribe from Observables.

### Using unsubscribe()

```typescript
subscription!: Subscription;

ngOnInit() {
  this.subscription = this.http.get('/users')
    .subscribe(data => console.log(data));
}

ngOnDestroy() {
  this.subscription.unsubscribe();
}
```

### Using takeUntil()

```typescript
destroy$ = new Subject<void>();

ngOnInit() {
  this.http.get('/users')
    .pipe(takeUntil(this.destroy$))
    .subscribe();
}

ngOnDestroy() {
  this.destroy$.next();
  this.destroy$.complete();
}
```

`takeUntil()` is commonly used when a component has multiple subscriptions because it can clean up all of them automatically.



>[!question] What are HTTP Interceptors?

`HTTP Interceptors` are Angular services that are used with HttpClient to intercept and modify HTTP requests and responses globally. 

They are commonly used for cross-cutting concerns that should apply to all API calls, for example Adding JWT Tokens, logging, global error handling, and request/response transformation.
### Example

```typescript
import {
  HttpInterceptorFn
} from '@angular/common/http';

export const authInterceptor: HttpInterceptorFn = (
  req,
  next
) => {

  const modifiedReq = req.clone({
    setHeaders: {
      Authorization: 'Bearer token'
    }
  });

  return next(modifiedReq);
};
```

### Register Interceptor

```typescript
provideHttpClient(
  withInterceptors([authInterceptor])
);
```

### How It Works

```text
Component
     ↓
Interceptor
     ↓
HTTP Request
     ↓
Server
     ↓
HTTP Response
     ↓
Interceptor
     ↓
Component
```


>[!question] What are Pipes? Pure vs Impure

Pipes are used to transform data directly inside Angular templates without modifying the original data in the TypeScript component.

Pipes also allow you to combine multiple expressions together, whether they're all values or some values and some declarations.

Angular provides many built-in pipes such as:

- UpperCasePipe
- lowercasePipe
- DatePipe
- CurrencyPipe

```html
<p>Price: {{ product.price | currency:'INR' }}</p>
<p>Price: {{ product.price | discount: 15 | currency : 'INR' }}</p>
```

>[!info] Pure Pipe

```typescript
@Pipe({
  name: 'myPipe'
})
```

A pure pipe executes only when the input value changes or the object reference changes. For example a primitive value changed (like String, Number, Boolean) or an object reference changed (like assigning a completely new Array or Object).

If an array or object is modified (e.g., push an item to an array users.push(newUser)) without changing its reference, the pure pipe will not run again. The pipe will not re-execute because the array reference remains the same.

---

>[!info] Impure Pipe


```typescript
@Pipe({
  name: 'myPipe',
  pure: false
})
```

An impure pipe executes during every change detection cycle -  (e.g., every keystroke or mouse click).

It detects changes even when objects or arrays are mutated without changing their reference. This can cause huge performance issues, so it's rarely used.

Also we can create custom pipes  using a TypeScript class decorated with `@Pipe` decorator and implementing the `PipeTransform` interface.

>[!question] 19 How do you create a Custom Pipe in Angular?

Sometime Angular doesn't have a built-in pipe for our specific use case, at the time we can easily create a custom pipe using a TypeScript class decorated with `@Pipe` decorator and implementing the `PipeTransform` interface.

A custom pipe must implement the `transform(value, ...args)` method, which receives the input value, alters it, and returns the result.

Create a pipe : We can create a custom pipe by running this in console : it will create us a pipe with `@Pipe` decorator and  implements `PipeTransform` by default.

```bash
 # syntax
ng generate pipe <pipe-name>

# create a custom pipe named `discount`
ng generate pipe discount
```

### Discount Pipe

```typescript
import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'discount'
})
export class DiscountPipe implements PipeTransform {

	 //write your custom pipe logic here
  transform(price: number, discountPercentage: number = 10): number {
    return price - (price * (discountPercentage / 100));
  }

}
```

### Import the Pipe

```typescript
@Component({
  imports: [CurrencyPipe, DiscountPipe]
})
```

### Usage

```html

<!-- transform( price = product.price,  discountPercentage = 10 (default)) -->
<p>Price: {{ product.price | discount | currency:'INR' }}</p>

<!-- transform( price = product.price,  discountPercentage = 20 ) -->
<p>Price: {{ product.price | discount:20 | currency:'INR' }}</p>

<!-- transform( price = product.price,  discountPercentage = 20 ) -->
<p>Price: {{ product.price | discount:30 | currency:'INR' }}</p>
```

### How it Works

```html
{{ product.price | discount:20 | currency:'INR' }}
```

1. Angular passes `product.price` to the `discount` pipe.
2. `20` is passed as the second argument.
3. The discounted price is calculated and returned.
4. The result is passed to the built-in `currency` pipe.
5. Angular formats and displays the final value as INR.

>[!question] 20. How do you optimize Angular performance?

Angular performance can be improved by reducing unnecessary rendering, minimizing bundle size, and optimizing change detection.

- `trackBy in ngFor` : `trackBy` helps Angular uniquely identify list items so only changed elements are updated instead of re-rendering the entire list.

```html
<li *ngFor="let user of users; trackBy: trackById">
  {{ user.name }}
</li>
```

---
- `Lazy Loading` : Loads feature modules only when required, reducing the initial application load time.
- `OnPush Change Detection` : Using `ChangeDetectionStrategy.OnPush` reduces unnecessary change detection cycles. Angular checks the component only when:
		- Input reference changes
		- An event occurs
		- An Observable emits a new value

```typescript
@Component({
  changeDetection: ChangeDetectionStrategy.OnPush
})
```

---

- `Avoid Heavy Functions in Templates` : Functions inside templates run on every change detection cycle, which can slow down the application. Instead, calculate values in the component and bind the result.

```html
<p>{{ calculateTotal() }}</p>
```

---
- `Code Splitting` : Split large applications into smaller feature modules to reduce bundle size and improve loading performance.
- `Cache API Responses` : Store frequently used data to avoid repeated API calls.
- `Use Pure Pipes` : Pure pipes execute only when the input value changes, reducing unnecessary calculations.
- `Unsubscribe from Observables` : Prevent memory leaks by cleaning up subscriptions. Common approaches:
		- `unsubscribe()`
		- `takeUntil()`
		- `async` pipe

>[!question] 21. What is Change Detection? Default vs OnPush Strategy

Change Detection is the process by which Angular detects changes in application data and automatically updates the UI.

Angular uses `Zone.js` to track asynchronous operations such as:
- User events
- HTTP requests
- Timers
- Promises

When an async operation completes, Angular runs a change detection cycle that:
1. Checks component data
2. Detects changes
3. Updates the UI if required

---

### Default Change Detection Strategy

In the Default strategy, Angular checks the entire component tree during every change detection cycle.

```typescript
@Component({
  changeDetection: ChangeDetectionStrategy.Default
})
```

It is simple and automatic, but can impact performance in large applications because many unnecessary checks may occur.

---

### OnPush Change Detection Strategy

In the OnPush strategy, Angular checks a component only when:
- An `@Input()` reference changes
- An event occurs inside the component
- An Observable emits a new value
- Change detection is triggered manually

```typescript
@Component({
  changeDetection: ChangeDetectionStrategy.OnPush
})
```

This reduces unnecessary checks and improves performance.

---

### trackBy with ngFor

When rendering lists, `trackBy` helps Angular uniquely identify items so that only changed elements are updated instead of re-rendering the entire list.

```html
<li *ngFor="let user of users; trackBy: trackById">
  {{ user.name }}
</li>
```


