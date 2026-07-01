>[!QUESTION] **1. What is Angular and how is it different from AngularJS?** 

Angular is a TypeScript-based frontend framework which is used for building single-page applications that requires no reload but the contain changes within the same page.

It is developed and maintained by Google.

Angular is a client side framework which allow developer to develop advanced web applications like Single-Page-Application.

It provides built-in features like components, routing, forms, dependency injection, and HTTP communication for developing scalable frontend applications.

>[!question] What are Single Page Applications (SPA)?

Single Page Applications (SPAs) are web applications that load a single HTML page once and dynamically update the content using TypeScript. 

This approach enables faster interactions and a smoother, more consistent user experience.


>[!question]  How many types of compilation Angular provides?

Angular provides two types of compilation:

**JIT (Just-in-Time) Compilation:***

- Compiles the Angular application at `runtime` inside the browser as it loads the application. 
- Faster development builds but slower performance in production.

**AOT (Ahead-of-Time) Compilation:***

-  Compiles the Angular application at `build time` before the browser downloads and runs the app in the browser. 
- Compiles the application into efficient JavaScript code ahead of time, 
- This makes the application load faster, reduces runtime errors, and improves overall performance compared to JIT (Just-in-Time) compilation,
- Recommended for production builds.


> [!QUESTION] ** New Angular vs old AngularJs **

| **AngularJS**                                                                                                                                                               | **Angular**                                                                                                     |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| It is old Javascript based framework.                                                                                                                                       | It is new and supports both TypeScript & Javascript                                                             |
| AngularJS uses MVC architecture, where the Model contains the business logic, the Controller processes information and the View shows the information present in the Model. | Angular replaces controllers with Components. Components are nothing but directives with a predefined template. |
| AngularJS provide limited mobile browser support.                                                                                                                           | Angular is supported by all popular mobile browsers.                                                            |
| Relatively slower due to dynamic compilation                                                                                                                                | Higher performance with AOT compilation                                                                         |
| Two-way data binding with scopes and watchers                                                                                                                               | Two-way data binding with reactive forms and observables                                                        |
> [!QUESTION] **2. What are Components in Angular?**

`Components` : Components are the basic building blocks of an Angular application. It is used to create reusable UI elements and define the structure and behavior of the app. It consists of

- HTML (Template)
    
- TypeScript (Logic)
    
- CSS (Styling)

- For example, navbar, login page, sidebar, or user profile can each be separate components.

```typescript
@Component({
  selector: 'app-home',
  templateUrl: './home.component.html'
})
export class HomeComponent {
}
```

---

 >[!question] What is the purpose of NgModule / Modules in Angular?

`Modules` : Modules are used to organize related components, services, directives, and pipes into a logical group of an Angular application.

Modules enables better code organisation, improves maintainability and enables lazy loading. Modules can export and import components from other components.

```typescript
@NgModule({
declarations: [ HomeComponent, ProductComponent ],
imports: [BrowserModule],
providers: [ProductService]
})

export class AppModule { }
```

`Modern Angular` :

With Standalone Components (Angular 15+), many applications no longer require feature modules, and components can manage their own dependencies directly.

In older Angular applications, `NgModule` was commonly used through `app.module.ts` to manage application structure and dependencies.


> [!question] **11. What is Angular CLI?**

`Angular CLI (Command Line Interface)` is a tool that helps developers create, manage, build, and maintain Angular applications using simple commands.

It automates many common development tasks and reduces boilerplate code.

`Common Commands` :

```bash
# Creates a new Angular project.
ng new my-app

# Starts the development server and runs the application locally.
ng serve

#Generates Angular artifacts such as components, services, pipes, and directives.
ng generate component home

# Builds the application for deployment.
ng build

ng test

ng lint
```

---

>[!QUESTION] **3. What is Data Binding? Explain Types** 

Data Binding in Angular is the process of connecting the TypeScript data with the HTML UI. It helps synchronize data between the component and the view automatically.

> [!EXAMPLE]  There are mainly 4 types of data Binding in Angular:

- **Interpolation / String Interpolation  : `{{ }}` :**  Used to display data from the TS model to the UI (HTML).

```typescript
	name : string = "Soutick";
```

```html
	<p>Welcome{{name}}</p>
```
---
- **Property Binding : `[ ]` :**  Used to send data from component to HTML element properties (href, src, style, value etc).
```typescript
	logoUrl : string = "https://angular.io/angular.svg";
	isImageDisabled : boolean = true;
```

```html
	<img [src] = "logoUrl">
	<button [disabled] = "isImageDisabled">submit</button>
```

---
- **Event Binding : `( )` : Event Binding** is the exact opposite of property binding. It listens to user actions in the DOM (like clicks, keystrokes, mouse hovers) and sends data from the DOM to the Component. Here if user click this button internally this `enableButton()` function will be called.

```HTML
	<button (click) = "enableButton()">Click Me</button>
```

```typescript
	 isImageDisabled: boolean = true;
	 enableButton() {
		 this.isImageDisabled = !this.isImageDisabled;
	 }
```
---
**Two-way data Binding : `[(ngModel)]`** If you update a variable in TypeScript, the HTML input updates. If the user types in the HTML input, the TypeScript variable updates instantly. Used for both displaying and updating data between UI and component using ngModel.

```HTMl
	<input type = "text" [(ngModel)] = "searchQuery">
	<p>searching for : {{searchQuery}}</p>
```

```Typescript
  searchQuery : string = '';
```
---
>[!QUESTIOn] **4. What are Directives? Types** 

- Directives in Angular are Class that is used to add dynamic behavior to the DOM (HTML elements)
- They are used to modify the **behavior, structure, or appearance** of HTML elements without writing manual DOM manipulation code.
- They help handle conditions, loops, styling, and custom behavior directly inside templates.

> [!EXAMPLE]   Angular mainly provides 3 types of directives.

1️⃣ Component Directives : These are the most commonly used directives in Angular. 

Instead of `@Directive` decorator we use `@Component` decorator to declare Component directives. These directives have a view, a stylesheet and a selector property.

Every component we create, such as **Home**, **Navbar**, or **Dashboard**, is technically a directive with its own template.

```typescript
@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrl: './home.component.cs'
})
export class HomeComponent {}
```

2️⃣ Structural Directives : Structural directives modify the DOM structure by adding, removing, or manipulating elements. Modern Angular prefers `@if`, `@for`, `@else`, and `@switch` over `*ngIf` and `*ngFor`. 

Modern Control Flow (Angular 17+)

```typescript
import { Component } from '@angular/core';

@Component({
  selector: 'app-products',
  templateUrl: './products.component.html'
})
export class ProductsComponent {

  products = [
    {
      id: 1,
      name: 'iPhone 17',
      isStockOut: false
    },{},{}
  ];

  trackById(index: number, product: any): number {
    return product.id;
  }

}
```


```html
@if(product.isStockOut) {
  <p>OUT OF STOCK!</p>
}

@for(product of products; track product.id) {
  <app-product-card [product]="product">
  </app-product-card>
}
```

`Legacy Angular`

```html
<div *ngIf="product.isStockOut">
  <p>OUT OF STOCK!</p>
</div>

<app-product-card
  *ngFor="let product of products; trackBy: trackById"
  [product]="product">
</app-product-card>
```



3️⃣ Attribute Directives : Attribute directives change the appearance or behavior of existing HTML elements without changing the DOM structure. 
Examples: [ngClass], [ngStyle]

```html
<input type="text" [(ngModel)]= "searchQuery">

<p [ngStyle]="{'color':'red'}">
	Error Message
</p>
<p [ngClass]="{'low-stock' : product.stock<3 }"> 
	{{ product.stock }}
</p>
```

>[!question] What are Services and Why Do We Use Them?

- Services in Angular are used to write reusable business logic, API calls, data handling, or shared functionality that can be used across multiple components.
- Instead of writing the same logic inside different components, we place it inside a service to improve **code reusability**, **maintainability**, and **separation of concerns**.
- Services commonly interact with the server by making AJAX/HTTP requests to backend APIs.

```typescript

@Injectable({ 
	providedIn: 'root' 
	})

export class ProductService {

	constructor(private http: HttpClient) { }

	getProducts(): any {
	return this.http.get<any[]>('http://127.0.0.1:8080/api/v1/products');
	}

	createProduct(newProduct: any) {
		return this.http.post('http://127.0.0.1:8080/api/v1/products', newProduct);
	
	}
	
	updateProduct(id: number, updatedProduct: any) {
		return this.http.put(`http://127.0.0.1:8080/api/v1/products/${id}`, updatedProduct);
		}
}
```

>[!Question] What is Dependency Injection?

- Dependency Injection (DI) is a design pattern where Angular automatically provides the required object or dependency to a class instead of the class creating it manually.
- It helps achieve loose coupling, easier testing, better code reusability, and a cleaner architecture.

>[!EXAMPLE] In Angular, usually there are two ways to inject dependencies ; 

>	1. `constructor` injection
>	2. `inject()` function.

 Suppose this is the Service class, Angular should create and inject the object in AppComponent. First we need to mark the class as `@Injectable`

`@Injectable()` : Marks the class as a service that can participate in Angular's Dependency Injection system.

```typescript

@Injectable({
  providedIn: 'root'
})
export class ProductService {

	  products = [{}, {}, {}];
	
	  getProducts(): any {
	    return this.products;
	  }

}
```

### `Constructor Injection` 

```typescript
export class AppComponent implements OnInit {

  constructor(private productService: ProductService) {
  }

  products: any[] = [];

  ngOnInit(): void {
    this.products = this.productService.getProducts();
  }

}
```

### Using `inject()` 

It access and inject dependencies directly within the component’s constructor or lifecycle methods without the need for constructor injection.

```typescript
export class AppComponent implements OnInit {

  private productService = inject(ProductService);

  products: any[] = [];

  ngOnInit(): void {
    this.products = this.productService.getProducts();
  }

}
```

>[!question] What are Lifecycle Hooks?

In Angular, components have a lifecycle: they are created, rendered, updated, and eventually destroyed.

Lifecycle Hooks are special methods provided by Angular that allow us to execute code at different stages of a component's lifecycle, such as component creation, rendering, updating, and destruction.

> [!EXAMPLE]  Important Lifecycle Hooks

1.  `ngOnInit` : Called once after Angular initializes the component. Commonly used for: API calls, Initial data loading, Component initialization. 

```typescript	
	ngOnInit() {
		this.loadUsers();
	}
```


---

2. `ngOnChanges` : Called whenever an `@Input()` property changes.

```typescript
ngOnChanges(changes: SimpleChanges) {
  console.log(changes);
}
```

---
3. `ngOnDestroy` : Called exactly once before Angular destroys the component. Used for cleanup activities such as unsubscribing from Observables, clearing timers, and removing event listeners.

```typescript
ngOnDestroy() {
  this.subscription.unsubscribe();
}
```

### Lifecycle Flow

```text
Component Created
       ↓
Constructor
       ↓
ngOnChanges
       ↓
ngOnInit
       ↓
Component Running
       ↓
ngOnDestroy
```

>[!QUestion] **Constructor vs ngOnInit**

### `Constructor` : 

The constructor is used for object initialization and Dependency Injection.  It is called immediately when Angular creates the component instance. It should not contain complex logic or API calls. 

Why? Because when the constructor runs, the component's inputs and UI elements are not fully ready yet. It is called immediately when the component class is created. 


```typescript
export class AppComponent implements OnInit {

  constructor(private productService: ProductService) {
  }

  products: any[] = [];

  ngOnInit(): void {
    this.products = this.productService.getProducts();
  }

}
```

### `ngOnInit` :

ngOnInit() is an Angular lifecycle hook that runs after constructors when Angular has initialized the component's input properties (@Input()). It is mainly used for

- API calls
- Loading initial data
- Component initialization logic
- Subscribing to Observables

---
>[!QUestion] What is Routing in Angular?

- Routing in Angular is used for navigation between different components in a single-page application without reloading the entire browser page.
- Angular Router maps URL paths to specific components.

```JAvascript
 const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'users', component: UserComponent }
];
```

>[!Question]  What is Lazy Loading?

 Lazy loading loads modules **only when it is required**, instead of loading everything initially. It Reduces initial load time and Improves performance 

```javascript
{   
 path: 'admin',   
 loadChildren: () => import('./admin.module')   
}
```


> [!question] **11. What is router-outlet?**

`router-outlet` is a built-in Angular directive that acts as a placeholder where routed components are displayed based on the URL.

When a user navigates to a route, Angular loads the corresponding component and renders it inside the `<router-outlet>`.

```html
<router-outlet></router-outlet>
```

`Example` :

```typescript
const routes: Routes = [
  { path: 'home', component: HomeComponent },
  { path: 'about', component: AboutComponent }
];
```

```html
<nav>
  <a routerLink="/home">Home</a>
  <a routerLink="/about">About</a>
</nav>

<router-outlet></router-outlet>
```

`How It Works` :

- `/home` → `HomeComponent`
    
- `/about` → `AboutComponent`
    
- Angular displays the matching component inside the `router-outlet`.
    

---

`Nested router-outlet` :

A `router-outlet` can be placed inside another routed component to support child routes.

```html
<!-- dashboard.component.html -->
<h2>Dashboard</h2>

<router-outlet></router-outlet>
```

---

`Mental Model` :

```text
URL
 ↓
Route
 ↓
Component
 ↓
router-outlet
```

Without a `router-outlet`, Angular has no place to display routed components.
<router-outlet></router-outlet>
----


>[!question] Explain Dynamic Components in Angular

`Dynamic Components` are components that are created and inserted into the application at runtime instead of being declared directly in the HTML template.

They are useful when the component to be displayed is not known during development and must be determined dynamically while the application is running.

Example Use Cases - Modal Dialogs, Notifications, Dynamic Dashboards, Plugin Systems, Dynamic Forms

```typescript
@ViewChild('container', {
  read: ViewContainerRef
})
container!: ViewContainerRef;

this.container.createComponent(UserComponent);
```

```html
<ng-container #container></ng-container>
```

Angular creates `UserComponent` at runtime and inserts it into the `ng-container`.

---

>[!question] What is Angular Material?

`Angular Material` is a UI component library for Angular that provides pre-built, reusable, and customizable UI components based on Google's Material Design guidelines.

It helps developers build modern, responsive, and consistent user interfaces without creating components from scratch.

### Installation

```bash
ng add @angular/material
```

### Common Components

- Buttons
- Cards
- Dialogs
- Tables
- Forms
- Toolbar
- Menu
- Snackbar
- Date Picker

### Example

```html
<button mat-raised-button color="primary">
  Save
</button>
```


> [!question] **14. What are Decorators and their types in Angular?**

`Decorators` are special annotations in Angular (prefixed with `@`) that provide metadata about a class, property, method, or parameter. They tell Angular how a particular class or member should behave.

Examples:

```typescript
@Component({...})
@Injectable({...})
@Input()
@Output()
```

---

`Class Decorators` : Used on classes to tell Angular what the class represents.

Common Class Decorators:

- `@Component`
- `@Injectable`
- `@Directive`
- `@Pipe`
- `@NgModule`

```typescript
@Component({
  selector: 'app-home'
})
export class HomeComponent {}
```

```typescript
@Injectable({
  providedIn: 'root'
})
export class ProductService {}
```

---

`Property Decorators` : Used on class properties. 

Common Property Decorators:

- `@Input`
- `@Output`
- `@ViewChild`
- `@ContentChild`

```typescript
@Input() product: any;

@Output() productBought = new EventEmitter();
```

---

`Method Decorators` : Used on methods to add extra behavior.

```typescript
@HostListener('click')
onClick() {
  console.log('Clicked');
}
```

---

`Parameter Decorators` : Used on constructor parameters to control dependency injection.

```typescript
constructor(
  @Optional() private loggerService: LoggerService
) {}
```

Common Parameter Decorators:

- `@Inject`
- `@Optional`
- `@Self`
- `@SkipSelf`
- `@Host`
---


>[!question] What is Client-Side Rendering (CSR) vs Server-Side Rendering (SSR)?

`Client-Side Rendering (CSR)` : Rendering happens in browser, the browser downloads a minimal HTML page and JavaScript files. Angular then runs in the browser, fetches data, and renders the UI.

```text
Browser
    ↓
Downloads HTML + JS
    ↓
Angular Runs
    ↓
Fetch Data
    ↓
Render UI
```

`Example` :
- Traditional Angular SPA
- React SPA

`Benefits` :
- Fast page navigation after initial load
- Reduced server load
- Rich interactive UI

`Drawbacks` :
- Slower first page load
- Poor SEO (without extra configuration)
- Blank screen until JavaScript loads

---

`Server-Side Rendering (SSR)` : Rendering happens on server, The server generates the HTML and sends a fully rendered page to the browser.

```text
Browser Request
       ↓
Server Renders HTML
       ↓
Send Complete HTML
       ↓
Browser Displays Page
```

`Example` :
- Angular Universal / Angular SSR
- Next.js

`Benefits` :
- Faster initial page load
- Better SEO
- Better social media previews

`Drawbacks` :
- More server processing
- More complex setup

---

`Key Difference`

| Client-Side Rendering (CSR)  | Server-Side Rendering (SSR) |
| ---------------------------- | --------------------------- |
| Rendering happens in browser | Rendering happens on server |
| Slower first load            | Faster first load           |
| SEO is harder                | Better SEO                  |
| Less server work             | More server work            |
| Good for dashboards/SPAs     | Good for public websites    |

---

> [!question] Can Angular render applications on the Server Side?

By default, Angular uses **Client-Side Rendering (CSR)**, where the browser downloads JavaScript and renders the UI.

Angular also supports **Server-Side Rendering (SSR)** using **Angular Universal** (now part of Angular SSR). With SSR, the server generates the HTML and sends a fully rendered page to the browser.

```text
Browser Request
       ↓
Angular Server
       ↓
Render HTML
       ↓
Send Complete Page
       ↓
Browser Displays Content
```

`Benefits of SSR` :

- Faster initial page load
    
- Better user experience for first-time visitors
    
- Improved SEO because search engines can read the rendered HTML
    
- Better social media previews when sharing links

---