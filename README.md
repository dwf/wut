# wut
*The Wunderlist Urwid Terminal.*

A console-based Wunderlist client written in Python using the
[Urwid](http://www.urwid.org/) library.

Requires:

* [hammock](https://github.com/kadirpekel/hammock)
* [urwid](http://urwid.org/)
* [pyyaml](http://pyyaml.org/)

Expects a YAML config at the location specified by `WUT_CONFIG_PATH` (or
`~/.wutrc` by default if that environment variable is not set) with the
following keys:

 * `client_id` -- Wunderlist client ID
 * `access_token` -- Wunderlist API token
