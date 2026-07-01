---
email: 
phone: 
birthday: 
street address: 
city: 
state: 
zip: 
country: 
tags: 
  - {{VALUE:Tag}}
---
> [!discuss]+ To Discuss with {{VALUE:First Name}}
> ```tasks
> not done
> (tag includes #discuss) AND (tag includes #{{VALUE:Tag}})
> hide tags
> short mode
> ```

> [!attention]+ Waiting for {{VALUE:First Name}}
> ```tasks
> not done
> (tag includes #waiting) AND (tag includes #{{VALUE:Tag}})
> hide tags
> short mode
> ```

> [!todo]+ Assigned to {{VALUE:First Name}}
> ```tasks
> not done
> description includes [[{{VALUE:First Name}} {{VALUE:Last Name}}]]
> hide tags
> short mode
> ```

## Meeting Notes

```base
filters:
  and:
    - attendees.contains(link("{{VALUE:First Name}} {{VALUE:Last Name}}"))
properties:
  file.name:
    displayName: Meeting Notes w/ {{VALUE:First Name}}
  note.date:
    displayName: Date
views:
  - type: table
    name: Table
    order:
      - file.name
      - date
    sort:
      - property: date
        direction: DESC
    columnSize:
      file.name: 594
```

## Notes