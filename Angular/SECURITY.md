
>[!question] 40. What is XSS and how does Angular prevent it?

`XSS (Cross-Site Scripting)` is a security vulnerability where malicious JavaScript code is injected into a web application and executed in a user's browser.

Example:

```html
<script>alert('Hacked')</script>
```

If user input is rendered without validation, the browser may execute the script.

---

`How Angular Prevents XSS` : Angular provides built-in sanxxitization and automatically treats template values as untrusted.

Before rendering data into the DOM, Angular sanitizes:
- HTML
- URLs
- Styles

This prevents malicious scripts from being executed.

```html
<p>{{ userInput }}</p>
```

Even if `userInput` contains a script tag, Angular escapes it instead of executing it.

---

`Common Protection Mechanisms` :
- Automatic HTML sanitization
- URL sanitization
- Style sanitization
- Escaping untrusted values

`Mental Model` :

```text
User Input
     ↓
Angular Sanitization
     ↓
Safe DOM Rendering
```

>[!question] What are Angular Guards?

`Angular Guards` are services used to control access to routes and navigation within an Angular application.

They are used to protect routes from unauthorized access or to prevent unwanted navigation, when certain conditions are not met.

### Common Types of Guards

`CanActivate` : Determines whether a route can be activated.

```text
User Tries to Open Route
        ↓
`CanActivate` Checks Permission
        ↓
Allow or Block Access
```

**Use Case:** Authentication and authorization

---

`CanDeactivate` : Determines whether a user can leave the current route.

```text
User Tries to Leave Page
        ↓
CanDeactivate Checks Condition
        ↓
Allow or Prevent Navigation
```

**Use Case:** Unsaved form changes

---

`CanLoad` : Determines whether a lazy-loaded module can be loaded.

```text
User Tries to Access Module
        ↓
CanLoad Checks Permission
        ↓
Load or Block Module
```

**Use Case:** Protecting lazy-loaded modules

---

### Example

```typescript
export const authGuard: CanActivateFn = () => {
  return inject(AuthService).isLoggedIn();
};
```

### Common Use Cases

- Authentication
- Authorization
- Preventing access to protected routes
- Warning about unsaved changes
- Protecting lazy-loaded modules

---

`Mental Model` :

```text
User Navigation
        ↓
Guard Executes
        ↓
Allow or Block Route
```

>[!question] Scenario: Implementing Route Guards for Authentication


Some routes should only be accessible to authenticated users. If an unauthenticated user tries to access a protected route, they should be redirected to the login page.

### Solution

Use an Angular `CanActivate` Guard to check whether the user is authenticated before allowing access to the route.

### Example

```typescript
import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { AuthService } from './auth.service';

export const authGuard: CanActivateFn = () => {

  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isLoggedIn()) {
    return true;
  }

  router.navigate(['/login']);
  return false;
};
```

### Configure Routes

```typescript
const routes: Routes = [
  {
    path: 'dashboard',
    component: DashboardComponent,
    canActivate: [authGuard]
  }
];
```

### How It Works

```text
User Requests Route
         ↓
     CanActivate
         ↓
  Authenticated?
      /      \
    Yes       No
     ↓         ↓
Allow Route  Redirect Login
```

### Benefits

- Protects sensitive routes
- Prevents unauthorized access
- Centralizes authentication logic
- Improves application security



>[!question] 41. How do you test components with Input/Output?

Components using `@Input()` and `@Output()` are tested by verifying data flow between parent and child components.

`Testing @Input()` : Pass mock data to the component and verify that the component receives and displays the data correctly.

```typescript
component.username = 'Soutick';

fixture.detectChanges();
```

Then verify that the UI is updated as expected.

---

`Testing @Output()` : Verify that the component emits the expected event and data.

```typescript
spyOn(component.productBought, 'emit');

component.buyProduct();

expect(component.productBought.emit)
  .toHaveBeenCalledWith(1);
```

Angular testing utilities commonly used:
- `TestBed`
- `fixture`
- `spyOn()`

`Mental Model` :

```text
@Input()
↓
Verify incoming data

@Output()
↓
Verify emitted events
```