>[!question] 32 Signals vs RxJS — When to Use What?

Signals and RxJS are both used for reactive programming in Angular, but they solve different problems.

Signals : Signals are Angular's built-in reactive state management mechanism used for managing local UI state. When a signal value changes, Angular automatically updates the UI.

```typescript
count = signal(0);

this.count.set(1);
```

**Use Cases:**
- Local component state
- UI toggles
- Counters
- Form state
- Derived UI values

---

`RxJS` : RxJS is a reactive library used for handling asynchronous streams and complex event-based operations.

```typescript
this.http.get('/users')
  .subscribe(data => console.log(data));
```

**Use Cases:**
- HTTP calls
- Search/autocomplete
- WebSockets
- Form value changes
- Event streams
- Complex async workflows

---

| Signals | RxJS |
|----------|------|
| Local state management | Async stream management |
| Simpler API | Powerful operators |
| UI-focused | Event and data stream focused |
| Synchronous reactivity | Asynchronous reactivity |

### Rule of Thumb

```text
Signals → State

RxJS → Async Operations
```

>[!question] 33 What are computed signal and effect signal?

`computed()` and `effect()` are reactive features built on top of Angular Signals.

```text
computed() -> Returns a calculated value

effect() -> Executes logic when values change
```

`computed()` : A computed signal derives a new value from one or more signals automatically. 

**Use Case:** Derived or calculated state

```typescript
count = signal(10);

//Whenever `count` changes, `doubleCount` is recalculated automatically.
doubleCount = computed(() => this.count() * 2);
```

---

`effect()` :  An `effect()` is used to perform side effects (executing logic) whenever signal values change.
**Use Cases:**
- Logging
- API calls
- Local Storage updates
- Triggering side effects

```typescript
count = signal(0);

//Whenever `count` changes, the effect runs automatically.
effect(() => {
  console.log(this.count());
});
```

---
>[!question] 34 How does Change Detection work with Signals?

Angular Signals integrate directly with Angular Change Detection and provide fine-grained reactive updates.

When a signal value changes, Angular automatically tracks which components or templates are using that signal and updates only those affected parts of the UI.

```typescript
count = signal(0);

increase() {
  this.count.set(this.count() + 1);
}
```

```html
<p>{{ count() }}</p>
```

When `count` changes, Angular automatically updates only the UI that depends on `count`.

---

### Traditional Change Detection

```text
Signal Changes
      ↓
Angular checks many components
      ↓
UI Updates
```

---

### Signal-Based Change Detection

```text
Signal Changes
      ↓
Angular knows exactly who uses it
      ↓
Only affected UI updates
```

---

### Benefits

- Fine-grained updates
- Fewer unnecessary checks
- Better performance
- More predictable UI updates

>[!question] 35 Why are Functions in Templates Bad but Pipes Good?

Why Functions in Templates are bad?

Functions inside templates execute during every change detection cycle.

```html
<p>{{ calculateTotal() }}</p>
```

Every time Angular runs change detection, `calculateTotal()` is executed again, even if the underlying data has not changed.

This can lead to:
- Unnecessary computations
- Repeated executions
- Slow rendering
- Performance issues in large applications

---

Why Pipes in Templates are good?

Pure pipes execute only when their input value changes. Therefore, Pipes are optimized for Angular's change detection mechanism

```html
<p>{{ price | currency:'INR' }}</p>
```

Angular caches the result and avoids unnecessary recalculations during every change detection cycle.

### Why Pipes Are Better

- Execute only when input changes
- Cached by Angular
- Better performance
- Cleaner templates

>[!question] 36 How do you structure large Angular applications?

Large Angular applications are typically organized using a feature-based architecture to improve scalability, maintainability, and code organization.

```text
src/app
├── core
├── shared
├── features
├── interceptors
├── guards
├── models
├── state
```

`Core` : Contains application-wide singleton services and functionality.

Examples:
- Authentication
- Global services
- Route guards
- HTTP interceptors

---

`Shared` : Contains reusable components, directives, and pipes used across multiple features.

Examples:
- Buttons
- Tables
- Form controls
- Custom pipes

---

`Features` : Contains business-specific functionality.

Each feature is organized in its own folder.

Examples:

```text
features
├── users
├── dashboard
├── products
├── admin
```

Each feature contains its own:
- Components
- Services
- Routes
- Models

---

`Services` : Business logic and API communication should be placed in services rather than components.

```typescript
this.userService.getUsers();
```

---

`State` : Manages shared application data.

Common approaches:
- Signals
- BehaviorSubject
- NgRx

>[!question] 37. How do you manage Global vs Local State?

In Angular, state is typically divided into Local State and Global State.

`Local State` : Component-specific data used only within a single component or a small component tree.

Examples:
- Form inputs
- Modal visibility
- UI toggles
- Selected tab

Commonly managed using:
- Component properties
- Signals
- `@Input()`
- `@Output()`

---

`Global State` : Shared data that needs to be accessed by multiple unrelated components across the application.

Examples:
- Logged-in user information
- Authentication status
- Shopping cart
- Application settings

Commonly managed using:
- Shared Services
- BehaviorSubject
- Signals
- NgRx

---

`Best Practice` : Keep state local whenever possible. Move state to a global solution only when multiple unrelated components need to access or synchronize the same data.

>[!question] 38 What is ControlValueAccessor?

`ControlValueAccessor (CVA)` is an Angular interface used to create custom form controls that work like built-in form elements such as `<input>`, `<select>`, and `<textarea>`.

It acts as a bridge between Angular Forms and custom components, allowing the custom component to participate in Angular's Forms API.

`Why do we need it?` : Angular automatically understands native form controls, but it does not know how to interact with custom components. ControlValueAccessor teaches Angular how to read and write values from a custom component.

`Supports` :
- `ngModel`
- Reactive Forms
- Form Validation
- Disabled State
- Touched State

`Common Use Cases` :
- Custom Dropdown
- Date Picker
- Rating Component
- Reusable Input Component
- Rich Text Editor

`Mental Model` :

```text
Angular Form
      ↕
ControlValueAccessor
      ↕
Custom Component
```

Without CVA, Angular Forms cannot communicate properly with custom form components.

>[!question] 39. What is InjectionToken?

`InjectionToken` is used to inject dependencies that are not classes, such as configuration values, constants, strings, objects, or application settings.

Angular's Dependency Injection system can automatically inject classes, but for non-class values, an `InjectionToken` is required.

### Create an InjectionToken

```typescript
export const API_URL = new InjectionToken<string>('apiUrl');
```

### Provide a Value

```typescript
providers: [
  {
    provide: API_URL,
    useValue: 'http://localhost:8080'
  }
]
```

### Inject the Value

```typescript
constructor(
  @Inject(API_URL) private apiUrl: string
) {}
```

`Common Use Cases` :
- API URLs
- Application Configuration
- Environment Settings
- Feature Flags
- Global Constants

`Mental Model` :

```text
Class Dependency
↓
UserService

Non-Class Dependency
↓
InjectionToken
```