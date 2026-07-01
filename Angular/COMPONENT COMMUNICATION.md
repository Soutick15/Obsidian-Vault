>[!question] 22. How do you pass data between components?

**Context :** In the frontend, we don't build one massive HTML page. Instead, we build small, reusable components (like buttons, search bars, or user cards) and assemble them. 

For this small reusable components to work together, components need to communicate with each other.

Data can be passed between Angular components using multiple approaches depending on the relationship between components.


### Parent → Child using @Input()

`@Input()` is used to pass data from a parent component to a child component.

**Parent Component**

```typescript
product = {
  name: 'iPhone 17'
};
```

```html
<app-product-card [prod]="product">
</app-product-card>
```

**Child Component**

```typescript
@Input({ required: true }) prod: any;
```

```html
<h2>{{ prod.name }}</h2>
```

---

### Child → Parent using @Output()

 In Angular, a child component does not pass data upwards directly. Instead, it emits an event. 
 
 The parent listens for this custom event. Using @Output() with EventEmitter we can send data (events/messages) from child to parent.

**Child Component**

```typescript
@Output() productBought = new EventEmitter<number>();

buyProduct() {
  this.productBought.emit(this.product.id);
}
```

**Parent Component**

```typescript
totalNumbersInCart: number = 0;

onProductBought(productId: number) {
  this.totalNumbersInCart++;
}
```

```html
<app-product-card
  (productBought)="onProductBought($event)">
</app-product-card>
```

---

### Unrelated Components

When components are not directly related (not parent-child), data is commonly shared using a service with `Subject` or `BehaviorSubject`.

```typescript
private userData = new BehaviorSubject<User | null>(null);

userData$ = this.userData.asObservable();
```

>[!question] 24. ViewChild vs ContentChild

`ViewChild` and `ContentChild` are decorators used to access child elements or components, but they access different parts of a component.

### ViewChild

`ViewChild` is used to access elements, child components, or directives that exist inside the component's own template.

```typescript
@ViewChild('inputRef') input!: ElementRef;
```

```html
<input #inputRef>
```

The component can directly access and interact with this input element.

---

### ContentChild

`ContentChild` is used to access content projected from a parent component using `<ng-content>`.

**Parent Component**

```html
<app-card>
  <p #message>Hello Angular</p>
</app-card>
```

**Child Component Template**

```html
<div class="card">
  <ng-content></ng-content>
</div>
```

**Child Component**

```typescript
@ContentChild('message') message!: ElementRef;
```

The child component can access the content passed by the parent.

---

### Key Difference

| ViewChild                 | ContentChild               |
| ------------------------- | -------------------------- |
| Accesses own template     | Accesses projected content |
| Works with component view | Works with ng-content      |
| Content belongs to child  | Content comes from parent  |

>[!question] 25. What is State Management?

State Management is the process of managing and sharing application data across multiple components in a predictable way.

Examples of application state:
- Logged-in user information
- Shopping cart data
- Theme settings
- API response data

State management becomes important when multiple components need access to the same data.

### Small Applications

For simple applications, state can be managed using:
- `@Input()`
- `@Output()`
- Shared Services

### Large Applications

In enterprise applications, centralized state management solutions are commonly used:

- NgRx
- NGXS
- Akita

These libraries provide a central store where application state is managed and shared across components.

>[!question] 26. How does Zone.js work? When do you use NgZone.runOutsideAngular()?

`Zone.js` is a library used by Angular to track asynchronous operations such as:
- HTTP requests
- Timers (`setTimeout`, `setInterval`)
- User events
- Promises

When an async operation completes, `Zone.js` notifies Angular, which then runs change detection to update the UI.

### Problem

For high-frequency operations such as scrolling, mouse movement, or repeated timers, Angular may trigger change detection too often, causing unnecessary performance overhead.

### NgZone.runOutsideAngular()

`runOutsideAngular()` allows code to execute outside Angular's change detection mechanism.

```typescript
this.ngZone.runOutsideAngular(() => {
  setInterval(() => {
    console.log('Background task');
  }, 1000);
});
```

This prevents Angular from running change detection for every timer execution.

### Updating the UI

If a UI update is needed, re-enter Angular's zone using `run()`.

```typescript
this.ngZone.run(() => {
  this.value = 'Updated';
});
```

### Common Use Cases

- Scroll events
- Mouse move events
- Animations
- Repeated timers
- Third-party libraries


>[!question] 27. Explain Hierarchical Dependency Injection

Hierarchical Dependency Injection means Angular maintains multiple levels of injectors and resolves dependencies based on the component hierarchy.

When Angular needs a dependency, it first looks in the current component's injector. If not found, it moves upward through parent injectors until it finds a matching dependency.

### Service Scopes

#### Root Level

A single shared instance is available throughout the entire application.

```typescript
@Injectable({
  providedIn: 'root'
})
export class UserService {}
```

---

#### Component Level

A new service instance is created for that component and its children.

```typescript
@Component({
  providers: [UserService]
})
export class UserComponent {}
```

---

### Dependency Resolution Flow

```text
Child Component
      ↑
Parent Component
      ↑
Root Injector
```

Angular searches upward until the dependency is found.

### Benefits

- Controls the scope of services
- Allows service isolation when needed
- Prevents unwanted shared state
- Improves application organization

>[!question] 28 What are @Host, @Self, @SkipSelf, and @Optional?

These are Dependency Injection decorators used to control how Angular searches for dependencies in the injector hierarchy.

1. @Self() : It tells Angular to look for the dependency only in the current injector. If the dependency is not available in the current injector, Angular throws an error.

```typescript
constructor(
  @Self() private userService: UserService
) {}
```

---

2. @SkipSelf() : Tells Angular to skip the current injector and start searching from the parent injector. Useful when a component has its own service instance but needs the parent instance instead.

```typescript
constructor(
  @SkipSelf() private userService: UserService
) {}
```

---

3.  @Host() : Tells Angular to search for the dependency only up to the host component. Angular stops searching once it reaches the host component.

```typescript
constructor(
  @Host() private userService: UserService
) {}
```

---

3. @Optional() : Makes a dependency optional. If Angular cannot find the dependency, it injects `null` instead of throwing an error.

```typescript
constructor(
  @Optional() private loggerService: LoggerService
) {}
```

---
>[!question] 29 switchMap vs mergeMap vs concatMap vs exhaustMap

These RxJS operators are used when one Observable creates another Observable (commonly HTTP calls).

1. switchMap : Cancels the previous request and switches to the latest one. 
	**Use Case:** Search box, autocomplete - where only the latest request matters.

```typescript
search.valueChanges.pipe(
  switchMap(term => this.http.get(`/users?q=${term}`))
)
```

---

2. mergeMap : Runs all requests in parallel without cancelling any of them.
	**Use Case :**  When multiple independent API calls should execute in parallel.

```typescript
users$.pipe(
  mergeMap(user => this.http.get(`/users/${user.id}`))
)
```

---

3. concatMap : Executes requests one by one in sequence.
	 **Use Case:** When request order matters

```typescript
users$.pipe(
  concatMap(user => this.http.get(`/users/${user.id}`))
)
```

---

4. exhaustMap : Ignores new requests while the current request is still running.

```typescript
loginClick$.pipe(
  exhaustMap(() => this.authService.login())
)
```

**Use Case:** Login button, form submission, preventing duplicate requests

---
>[!question] 30 Subject vs BehaviorSubject vs ReplaySubject

`Subject`, `BehaviorSubject`, and `ReplaySubject` are RxJS subjects used to share data with multiple subscribers.

### Subject (No Memory)

```typescript
const subject = new Subject<number>();
```

A Subject does not store any previous values. Subscribers only receive values emitted after they subscribe. If a subscriber joins late, it will not receive old values.

**Use Case:** Event notifications

---
### BehaviorSubject (Remembers Latest Value)

```typescript
const subject = new BehaviorSubject<number>(0);
```

A BehaviorSubject stores the latest value and immediately sends it to new subscribers. It Requires an initial value.

**Use Cases:**
- Shared application state
- Logged-in user information
- Authentication status

---
### ReplaySubject (Remembers Multiple Values)

A ReplaySubject stores multiple previous values and replays them to new subscribers.

```typescript
const subject = new ReplaySubject<number>(2);
```

The number `2` means it will remember the last 2 emitted values.

**Use Case:** When new subscribers need previous data/history


>[!question] 31 How do you cancel HTTP requests?

In Angular, HTTP requests can be cancelled to avoid unnecessary API calls, improve performance, and prevent outdated responses from updating the UI.

-  `switchMap` : `switchMap` automatically cancels the previous request when a new request is triggered.

```typescript
search.valueChanges.pipe(
  switchMap(term =>
    this.http.get(`/users?q=${term}`)
  )
)
```

**Use Case:** Search box, autocomplete

---

 - `takeUntil` : `takeUntil()` cancels the request when the notifier emits a value.

```typescript
this.http.get('/users')
  .pipe(takeUntil(this.destroy$))
  .subscribe();
```

```typescript
ngOnDestroy() {
  this.destroy$.next();
  this.destroy$.complete();
}
```

**Use Case:** Automatically cancel requests when a component is destroyed

---

 - `unsubscribe()` : Manually cancels an active subscription.

```typescript
subscription = this.http.get('/users')
  .subscribe();

this.subscription.unsubscribe();
```

- **Use Case:** Manual cleanup of subscriptions