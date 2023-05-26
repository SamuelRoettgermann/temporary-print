# temporary-print

An extension for the `print` function which allows temporary printing,
of oneliners, which is how this project started, printing with 
delay before and/or after the call and a few more tweak options.

The base foundation for deleting the text is not to actually delete it
but to overwrite it with spaces. As you may guess yourself this isn't
the most efficient option, and it likely doesn't work on operating systems
other than Windows as it relies on carriage return (`'\r'`) characters.

The API is really simple, as it's just the `print` function.
This `print` function behaves exactly like the built-in `print`
function, but can be modified with additional flags like `delay`,
`post_delay`, `priority`, etc. There are also 4 additional functions
for special purposes or permanent changes:

* `set_display_time` - set how long temporary text will be displayed
* `is_running` - Tells whether there are still elements in 
the queue or currently being displayed
* `clear` - Clears the queue
* `set_refresh_rate` - advanced option, this controls the interval at 
which it is checked whether `display_time` has been exceeded. 
Setting this can help when dealing with long display times.
It is recommended to set this value to the maximal permitted
time inaccuracy.

Written in: Python 3.8

Bugs:
* Doesn't allow newlines or carriage returns even for persistent prints
