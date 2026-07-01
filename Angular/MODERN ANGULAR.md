>[!question] 42. What are Standalone Components?

`Standalone Components` are Angular components that can work independently without being declared inside an `NgModule`.

Before standalone components, every component had to be declared inside a module such as `AppModule`.

```typescript
//old way
@NgModule({
  declarations: [UserComponent]
})
export class AppModule {}
```

Modern Angular allows components to manage their own dependencies using the `imports` property.

```typescript

// new standalone way
@Component({
  selector: 'app-user',
  standalone: true,
  imports: [CommonModule]
})
export class UserComponent {}
```

`Benefits` :

- Less boilerplate code
- No need for most NgModules
- Simpler project structure
- Easier lazy loading
- Better code organization
- Easier to understand and maintain

`Mental Model` :

```text
Before
↓
Component + NgModule

Now
↓
Component manages itself
```

>[!question] What improvements have been made to Standalone Testing?

Angular has improved testing support for Standalone Components, making tests simpler and reducing setup code.

Previously :  components required creating and configuring testing modules (`TestBed`) with declarations and imports. 

After Standalone Components : Standalone Components can now be tested directly without creating unnecessary NgModules.

### Benefits

- Less boilerplate code
- Simpler test configuration
- Faster test setup
- Better tree-shaking
- Improved developer experience

### Example

```typescript
await TestBed.configureTestingModule({
  imports: [UserComponent]
}).compileComponents();
```

The Standalone Component is imported directly into the test without declaring it inside an NgModule.

---

`Angular 19 Improvements` :

- Better support for Standalone Components
- Simplified test configuration
- Faster test execution
- Improved integration with Jasmine and Karma

---

`Mental Model` :

```text
Before
↓
Component → Test Module → Test

Now
↓
Component → Test
```


> [!question] 45. Explain the use of Functional Components

Angular does not have React-style Functional Components. Angular components are class-based and use decorators such as `@Component`.

However, modern Angular encourages a more functional programming style through:

- Standalone Components
    
- Signals
    
- Functional Guards
    
- Functional Interceptors
    
- Functional Resolvers
    

The goal is to reduce boilerplate code and make components simpler, more reusable, and easier to test. Instead of creating a class-based guard, Angular allows a simple function-based approach.

```typescript
export const authGuard: CanActivateFn = () => {
  return inject(AuthService).isLoggedIn();
};
```

---

>[!question] 43. Search Optimization (Debounce + API Cancellation)


 `Problems Scenario` : User types in search box and A search API is called on every key press.
- Too many API calls
- Increased server load
- Poor performance
- Race conditions (older responses may arrive after newer ones)

`Solution` : Use `debounceTime()` and `switchMap()`.

`debounceTime()` : Waits for the user to stop typing before making the API call.

`switchMap()` : Cancels the previous API request when a new search term arrives.

### Example

```typescript
search$
  .pipe(
    debounceTime(300),
    switchMap(term => this.api.search(term))
  )
  .subscribe(result => {
    this.data = result;
  });
```

### How It Works

```text
User Types
↓
debounceTime(300)
↓
Wait 300ms
↓
switchMap()
↓
Cancel Previous Request
↓
Call Latest API
↓
Display Latest Result
```

`Benefits` :
- Reduces API calls
- Cancels unnecessary requests
- Prevents race conditions
- Improves user experience


>[!question] 44. Large List Performance Issue

### Scenario

A component displays thousands of records using `*ngFor` and the UI becomes slow.

### Solution

Use techniques such as `trackBy`, Pagination, and Virtual Scrolling.

`trackBy()` : Helps Angular uniquely identify list items so that only changed items are updated instead of re-rendering the entire list.

```html
<li *ngFor="let item of items; trackBy: trackById">
  {{ item.name }}
</li>
```

```typescript
trackById(index: number, item: any) {
  return item.id;
}
```

---

`Pagination` : Load and display records in smaller chunks instead of loading all data at once.

```text
Page 1 → 20 records
Page 2 → 20 records
Page 3 → 20 records
```

---

`Virtual Scrolling` : Render only the items currently visible on the screen instead of rendering the entire list.

```text
10,000 Records
      ↓
Only 20-30 Visible Items Rendered
```

### Benefits

- Reduces DOM rendering
- Improves UI responsiveness
- Reduces memory usage
- Improves application performance
>[!question] 45. Component Communication (Advanced)

### Scenario

Multiple unrelated components need to share data. In this case, we should use a Shared Service with `BehaviorSubject` or `Signals`.

`Shared Service` : Acts as a central place to store and share data between components.

`BehaviorSubject` : Stores the latest value and automatically sends it to new subscribers.

### Example

```typescript
@Injectable({
  providedIn: 'root'
})
export class DataService {

  private data = new BehaviorSubject<any>(null);

  data$ = this.data.asObservable();

  setData(value: any) {
    this.data.next(value);
  }

}
```

### How It Works

```text
Component A
      ↓
DataService
      ↓
BehaviorSubject
      ↓
Component B
      ↓
Component C
```

When one component updates the value, all subscribed components automatically receive the latest value.

### Benefits

- Enables communication between unrelated components
- Maintains a single source of truth
- Easy state sharing
- Reactive updates across the application

Parent → Child
↓
@Input()

Child → Parent
↓
@Output()

Unrelated Components
↓
Shared Service + BehaviorSubject / Signals

>[!question] 46. Memory Leak Issue

Scenario : The application becomes slower over time after prolonged usage.

Cause : This commonly happens when Observables continue running even after a component is destroyed.

Examples:
- HTTP subscriptions
- Timers
- WebSockets
- Form value subscriptions

### Solution

`unsubscribe()` : Manually unsubscribe in `ngOnDestroy()`.

`takeUntil()` : Automatically unsubscribe when a notifier emits a value.

`async` Pipe : Angular automatically manages subscription and cleanup.

### Example

```typescript
private destroy$ = new Subject<void>();

ngOnInit() {
  this.service.getData()
    .pipe(takeUntil(this.destroy$))
    .subscribe();
}

ngOnDestroy() {
  this.destroy$.next();
  this.destroy$.complete();
}
```

### Using Async Pipe

```html
<div>{{ users$ | async | json }}</div>
```

The `async` pipe automatically subscribes and unsubscribes when the component is destroyed.

### Benefits

- Prevents memory leaks
- Reduces unnecessary background processing
- Improves application performance
- Ensures proper cleanup of resources