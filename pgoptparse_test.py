#!/usr/bin/env python

from pgoptparse import PGOptionParser
import psycopg2

parser = PGOptionParser('usage: %prog [options] useless_arguments')
options, args = parser.parse_args()
conn_string = "dbname='%s' host='%s' user='%s' password='%s' port='%s' sslmode='disable'" % (options.database, options.hostname, options.username, options.password, options.port)
conn = psycopg2.connect(conn_string)
cur = conn.cursor()
cur.execute("SELECT 'This test worked, I guess.' as result")
results = cur.fetchall()
print results[0][0]
