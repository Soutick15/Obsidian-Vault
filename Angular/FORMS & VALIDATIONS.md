
>[!question] What is Template-driven and Reactive Forms

- **Template-driven Forms :** Template-driven Forms are old, HTML-heavy. They are Suitable for small forms. It uses `[(ngModel)]` Similar to old JS frameworks. Logic is mostly in HTML.

- **Reactive Forms :** Reactive Forms are modern Better for complex forms, More scalable, Logic handled in TypeScript . Reactive Forms are industry standard and Preferred in real projects.
- To use reactive forms we need to import the `ReactiveFormsModule`.
- We use `FormControl` to take a single input field (like a text name).  
- `FormArray` for multiple input for a single field.
- Then we use `FormGroup` is a collection of `FormControls`, Used to grab all the values as one big JSON object!

```javascript
import { Component } from '@angular/core';

import { ReactiveFormsModule, FormGroup, FormControl, Validators } from '@angular/forms';

@Component({

  selector: 'app-product-form',
  imports: [ReactiveFormsModule],
  templateUrl: './product-form.html',
  styleUrl: './product-form.css',

})

export class ProductForm {
  //A FormGroup is a collection of FormControls, Used to grab all the values as one big JSON object!

  productForm = new FormGroup({

    //A FormControl represents a single input field (like a text name).
    name: new FormControl('', [Validators.required, Validators.min(3)]),
    description: new FormControl('', [Validators.required]),
    price: new FormControl(0, [Validators.required, Validators.min(1)])

  });

  onSubmit() {
    if (this.productForm.valid) {
      console.log("Form is valid!data:", this.productForm.value);
      }
      else {
      console.log("Form is invalid!");
    }
  }
}
```

>[!question] **13. How do you handle Form Validation?** 

- Form validation in Angular is mainly handled using: Template-Driven Forms & Reactive Forms
- In `Reactive Forms` Form validation is commonly handled using built-in `Validators` class.

>[!example] Common Angular Validators methods:

```javascript
	Validators.required
	Validators.minLength(3)
	Validators.maxLength(12)
	Validators.email
	Validators.pattern()
```


>[!question] How do you create Custom Validators in Angular?

Angular supports two types of custom validators:

1.  Synchronous Validator (ValidatorFn) : Used when validation logic can be performed immediately.

```typescript
export function noAdminValidator(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    return control.value === 'admin'
      ? { forbiddenName: true }
      : null;
  };
}
```

---

2. Asynchronous Validator (AsyncValidatorFn) : Used when validation requires an API call or server check.

```typescript
import {
  AbstractControl,
  AsyncValidatorFn,
  ValidationErrors
} from '@angular/forms';

import { map } from 'rxjs/operators';

export function usernameValidator(
  service: UsernameValidatorService
): AsyncValidatorFn {

  return (control: AbstractControl) => {

    return service
      .checkUsername(control.value)
      .pipe(
        map(isAvailable =>
          isAvailable
            ? null
            : { usernameTaken: true }
        )
      );
  };
}
```

### Usage

```typescript
username: [
  '',
  [],
  [usernameValidator(this.usernameValidatorService)]
]
```