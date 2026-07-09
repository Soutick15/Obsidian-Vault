# REGULAR EXPRESSION

Regular expressions (RegEx) are patterns used to match character combinations in strings. They are commonly used for string matching, validation, and manipulation. Below is a detailed explanation and examples of regular expressions in SQL and their usage:

**Syntax for Regular Expressions in SQL**

- SQL supports regular expressions using the REGEXP operator in some databases (e.g., MySQL).
- Use REGEXP or RLIKE to apply regular expressions in WHERE clauses.

## The following table lists common regex symbols, their meanings and examples:

|Pattern|Description|Example|Matches|
|---|---|---|---|
|.|Matches any single character (except newline)|h.t|hat, hit, hot|
|^|Matches the start of a string|^A|Apple, Apricot|
|$|Matches the end of a string|ing$|sing, bring|
|\||Acts as logical OR|cat\|dog|cat, dog|
|*|Zero or more of previous character|ab*|a, ab, abb|
|+|One or more of previous character|ab+|ab, abb|
|?|Zero or one of previous character|colou?r|color, colour|
|{n}|Exactly n times|a{3}|aaa|
|{n,}|n or more times|a{2,}|aa, aaa|
|{n,m}|Between n and m times|a{2,4}|aa, aaa, aaaa|
|[abc]|Any one character inside|[aeiou]|a, e, i, o, u|
|[^abc]|Any character not inside|[^aeiou]|any non-vowel|
|[a-z]|Character range|[0-9]|0–9|
|\|Escapes special character|\.|.|
|\b|Word boundary|\bcat\b|cat (not scatter)|
|\B|Non-word boundary|\Bcat|scatter|
|(abc)|Grouping|(ha)+|ha, haha|
|\1|Back-reference|(ab)\1|abab|

## Common Regex Patterns are used to match and find specific text patterns.

|Pattern|Description|Example|Matches|
|---|---|---|---|
|^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$|Validates an email address.|john.doe@gmail.com|Valid email addresses|
|^[0-9]+$|Matches a numeric string only.|123456|123, 456, 7890|
|https?://[^ ]+|Matches a URL starting with http or https.|https://example.com/|URLs|
|^[A-Za-z0-9]+$|Matches alphanumeric strings.|User123|abc123, xyz789|

