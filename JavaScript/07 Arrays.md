# Array:

An array is a special type of object used to store multiple values in a single variable. Arrays can hold a collection of elements, such as numbers, strings, objects, or other arrays (nested arrays).

**Key features:**

- JavaScript arrays can store heterogeneous elements (different data types).
- Array elements are ordered, and each element has a numeric index.
- JavaScript arrays are dynamic, meaning you can change the Array size by adding or removing elements.

**Two ways we can create Arrays:**

**1.Using array literal:**

```javascript
let arr1 = [1, 2, 3, 4, 5]; // an array with numbers
let arr2 = ["apple", "banana", "mango"]; // array with strings
let arr3 = ["apple", 1, Boolean, undefined, null ]; // Collection of heterogeneous elements
```

**2.Using new Array() constructor:**

```javascript
let arr = new Array(5); // creates an array of length 5 with empty values
let arr2 = new Array("apple", "banana", "mango"); // creates an array with 3 strings
```

### Array Methods


```Javascript

let array = [1, 2, 3, 4, 5];

// forEach() - Executes a provided function once for each array element
array.forEach((item) => console.log(item));

// map() - Creates a new array populated with the results of calling a function on every element
let mappedArray = array.map((item) => item * 2); // [2, 4, 6, 8, 10]

// filter() - Creates a new array with elements that pass the test implemented by the provided function
let filteredArray = array.filter((item) => item > 2); // [3, 4, 5]

// reduce() - Executes a reducer function on each array element, resulting in a single value
let sum = array.reduce((acc, item) => acc + item, 0); // Sum of array elements: 15

// find() - Returns the first element that satisfies the provided testing function
let foundItem = array.find((item) => item === 3); // 3

// findIndex() - Returns the index of the first element that satisfies the provided testing function
let foundIndex = array.findIndex((item) => item === 3); // 2

// some() - Tests whether at least one element in the array passes the test
let hasSome = array.some((item) => item > 3); // true

// every() - Tests whether all elements in the array pass the test
let allPass = array.every((item) => item > 0); // true

// push() - Adds one or more elements to the end of an array and returns the new length
array.push(6); // [1, 2, 3, 4, 5, 6]

// sort() - Sorts the elements of an array in place and returns the array
let sortedArray = array.sort(); // [0, 2, 3, 4, 6, 7, 10]

// shift() - Removes the first element from an array and returns it
let firstElement = array.shift(); // Removes 1, returns 1

// unshift() - Adds one or more elements to the beginning of an array and returns the new length
array.unshift(0); // [0, 2, 3, 4, 5]

// indexOf() - Returns the first index at which a given element can be found
let index = array.indexOf(3); // 2

// includes() - Determines whether an array includes a certain value
let hasValue = array.includes(4); // true

// concat() - Merges two or more arrays and returns a new array
let newArray = array.concat([6, 7]); // [0, 2, 3, 4, 5, 6, 7]

// reverse() - Reverses the elements in an array
let reversedArray = array.reverse(); // [7, 6, 5, 4, 3, 2, 0]

// slice() - Returns a shallow copy of a portion of an array into a new array
let slicedArray = array.slice(1, 3); // [6, 5]

// splice() - Changes the content of an array by removing, replacing, or adding elements in place
array.splice(2, 1, 10); // [7, 6, 10, 4, 3, 2, 0]

// sort() - Sorts the elements of an array in place and return
```