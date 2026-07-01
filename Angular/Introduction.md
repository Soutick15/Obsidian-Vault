
Angular is a TypeScript-based frontend framework used to build Single Page Applications (SPA).

`Benefits` :

- Single Page Application development
    
- Component-based architecture
    
- Easy routing and navigation
    
- Unit testable code
    
- Dependency Injection support
    

---

# Prerequisites

## Node.js

Node.js provides a runtime environment to execute JavaScript outside the browser.

Check version:

```bash
node --version
```

---

## npm

npm (Node Package Manager) is used to install and manage JavaScript packages.

Check version:

```bash
npm --version
```

---

# Angular CLI

Angular CLI helps generate Angular projects, components, services, and boilerplate code automatically.

Install globally:

```bash
npm install -g @angular/cli
```

`Benefits` :

- Project generation
    
- Component generation
    
- Service generation
    
- Build and deployment commands
    
- Reduced boilerplate code
    

---

# Create Angular Project

Create a new Angular application:

```bash
ng new MyNewAngularApp
```

Navigate into project:

```bash
cd MyNewAngularApp
```

Start development server:

```bash
ng serve
```

Default URL:

```text
http://localhost:4200
```

---

# Install Bootstrap

Install Bootstrap:

```bash
npm install bootstrap
```

Install jQuery:

```bash
npm install jquery
```

Add Bootstrap CSS inside `angular.json`:

```json
"styles": [
  "src/styles.css",
  "./node_modules/bootstrap/dist/css/bootstrap.min.css"
]
```

Add Bootstrap JS and jQuery:

```json
"scripts": [
  "./node_modules/bootstrap/dist/js/bootstrap.js",
  "./node_modules/jquery/dist/jquery.js"
]
```

---

# Angular Project Structure

```text
src
├── app
├── assets
├── main.ts
├── styles.css

package.json
angular.json
```

---

## src/app

Contains application code.

```text
src/app
├── app.component.html
├── app.component.css
├── app.component.ts
├── app.component.spec.ts
```

---

## app.component.html

Contains the HTML structure of the component.

---

## app.component.css

Contains styles specific to the component.

---

## app.component.ts

Contains component logic and functionality.

---

## app.component.spec.ts

Contains unit test cases.

---

## src/styles.css

Global styles applied throughout the application.

---

## src/assets

Stores static resources.

Examples:

- Images
    
- Icons
    
- Fonts
    

---

# Important Configuration Files

## package.json

Manages project dependencies and scripts.

Examples:

- Angular packages
    
- Bootstrap
    
- jQuery
    

`Spring Boot Equivalent` :

```text
pom.xml
or
build.gradle
```

---

## angular.json

Main Angular CLI configuration file.

Used for:

- Build settings
    
- Global styles
    
- Scripts
    
- Assets
    
- Development server configuration
    

---

## src/main.ts

Application entry point.

Angular application starts (bootstraps) from here.

---

# Angular Components

Create component:

```bash
ng generate component user
```

Shorthand:

```bash
ng g c user
```

Using local CLI:

```bash
npx ng generate component user
```

---

# Root Component

```html
<app-root></app-root>
```

Root component loaded when application starts.

---

# Interpolation

Used to display TypeScript values inside HTML.

Component:

```typescript
myName = "Soutick";
```

Template:

```html
<h2>{{ myName }}</h2>
```

---

# Templates

Templates contain HTML and Angular template syntax.

Templates can access:

- Component properties
    
- Component methods
    
- Signals
    
- Expressions
    

---

# Angular Routing

Angular Routing enables navigation between views without reloading the page.

`Route` : Maps a URL to a component.

Example:

```text
/about  → AboutComponent
/contact → ContactComponent
```

---

# Base URL

Inside `index.html`:

```html
<base href="/">
```

---

# Router Link

Instead of:

```html
<a href="#">
```

Use:

```html
<a routerLink="/about" class="nav-link">
  About
</a>
```

---

# Configure Routes

```typescript
const routes: Routes = [
  { path: 'home', component: HomeComponent },
  { path: 'about', component: AboutComponent }
];
```

---

# Router Module

```typescript
@NgModule({
  imports: [
    RouterModule.forRoot(routes)
  ],
  exports: [
    RouterModule
  ]
})
export class AppRoutingModule {}
```

---

# Router Outlet

```html
<router-outlet></router-outlet>
```

`router-outlet` acts as a placeholder where Angular loads the component associated with the current route.