# Aim
To autogenerate type hints

# Description
Trace runtime and collect information on all arguments passed to functions.
Same for return values.
Second part of this project will take the collected data and will generate a list of all types based on the values it saw.
Final part will update existing code with the type notations based on what was discovered in second step.

# Notes to myself
1) Originally I wanted to have 3 separate steps:
- record data
- get the type information based on the recorded data
- update / modify files with the derived types and import statements

2) During implementation I realised that saving classes would be troublesome, as I only get a reference to them during runtime.
I decided to get the type information and drop the values, merging step one and two

3) Processing dicts, I've noticed that returnign 'Dict' is not very helpful -> it would be good to get the shape of nested structures.
Doing so will be 'complicated', and I feel like separating step 1  and 2 would be a wise thing to do.
But what about classses? Well, we can just record class name, and move on `CLASS:Name` should suffice, and we can deal
with that during the second step.
