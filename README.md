# wut
*The Wunderlist Urwid Terminal.*

A console-based Wunderlist client written in Python using the
[Urwid](http://www.urwid.org/) library.

Requires:

* [hammock](https://github.com/kadirpekel/hammock)
* [urwid](http://urwid.org/)
* [pyyaml](http://pyyaml.org/)

Expects a YAML config at `~/.wutrc` with the following keys:

 * `which_list` -- name of list to retrieve
 * `client_id` -- Wunderlist client ID
 * `token` -- Wunderlist API token
