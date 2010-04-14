# pglunchbox

This module provides a couple of convienence classes for use with scripting
against a PostgreSQL database.  PGOptionParser extends OptionParser from
optparse to add default options akin to psql's options.  PGOptionParser will
also parse your pgpass file, if present, by way of the PGPassFile class.

PGPassFile also has get_login and get_password methods, that will match the
following keyword arguments against lines in your pgpass file, and return
the first matching login and/or password:

* hostname
* port
* database
* username (needed for get_password)

[Derek Arnold](mailto:derek@dderek.com)

[http://dderek.com](http://dderek.com)
