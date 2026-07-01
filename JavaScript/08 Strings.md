# String Methods:

```javascript
let str = "JavaScript is awesome!";

// length
let length = str.length; // Returns the length of the string

// charAt()
let char = str.charAt(4); // Returns the character at index 4

// indexOf()
let index = str.indexOf("awesome"); // Returns the index of the word "awesome"

// lastIndexOf()
let lastIndex = str.lastIndexOf("JavaScript"); // Returns the last occurrence of "JavaScript"

// slice()
let sliced = str.slice(0, 10); // Extracts characters from index 0 to 9

// substring()
let substring = str.substring(0, 10); // Extracts characters from index 0 to 9

// substr()
let substr = str.substr(0, 10); // Extracts 10 characters starting from index 0

// toUpperCase()
let upperStr = str.toUpperCase(); // Converts the string to uppercase

// toLowerCase()
let lowerStr = str.toLowerCase(); // Converts the string to lowercase

// replace()
let replaced = str.replace("awesome", "fun"); // Replaces "awesome" with "fun"

// replaceAll()
let replacedAll = str.replaceAll("JavaScript", "JS"); // Replaces all instances of "JavaScript" with "JS"

// trim()
let trimmedStr = str.trim(); // Removes whitespace from both sides

// split()
let arr = str.split(" "); // Splits the string into an array based on spaces

// concat()
let newStr = str.concat(" Let's learn it!"); // Concatenates strings

// startsWith()
let starts = str.startsWith("JavaScript"); // Checks if string starts with "JavaScript"

// endsWith()
let ends = str.endsWith("!"); // Checks if string ends with "!"

// includes()
let includes = str.includes("awesome"); // Checks if "awesome" is in the string

// repeat()
let repeated = str.repeat(2); // Repeats the string twice
```