#!/usr/bin/env python

import psycopg2
import re

from pgoptparse import PGOptionParser

def main():
    """Test the pgoptparse module thoroughly."""
    parser = PGOptionParser('usage: %prog [options] useless_arguments')
    options, args = parser.parse_args()

    conn_string = parser.connection_string()
    clean_conn_string = re.sub("password='[^']*'", "password='*******'",
        conn_string)
    print "Our automatically generated connection string:\n%s\n" % \
        (clean_conn_string)

    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()
    cur.execute("SELECT 'This test worked, I guess.' as result")
    results = cur.fetchall()

    print "Test Query results:\n%s" % results[0][0]


if __name__ == "__main__":
    main()
