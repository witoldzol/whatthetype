# make sure we presever order of arguments! 
# identify 'self' & 'cls' aka first arg of class method, and give it 'special' arg,
so that we can skip it in 3rd step when we are upating function defs!
or identify if method or free funct using `inspect` module & `ismethod()` or `isfunction()`
# CLI: add arguments to run step 1 / 2 / 3 ?
# create a warning if an argument in a function takes two or more different types of input
foo(int|str) : this might be an indication of a bug
# save step 1 output to a file?
