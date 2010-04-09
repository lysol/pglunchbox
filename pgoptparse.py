import os
import stat
from optparse import * 
from platform import system
from getpass import getpass, getuser, GetPassWarning



class PGOptionParser(OptionParser):
    """Extends OptionParser to add psql-like options and other conveniences."""

    def __dict_coalesce(self, dict_1, dict_2):
        """This may be an example of cargo cult programming."""

        payload = {}
        for key in dict_2.keys():
            if dict_1.has_key(key):
                payload[key] = dict_1[key]
            else:
                payload[key] = dict_2[key]
        return payload

    def __pg_defaults(self):
        """Parse environmental variables like PGPASS, etc."""

        defaults = { 'PGPORT': 5432, 'PGDATABASE': getuser(),
                     'PGHOST': 'localhost', 'PGUSER': getuser() }

        return self.__dict_coalesce(os.environ, defaults)

    def __read_pgpass(self):
        """Read the file located in self.pgpass and parse it, setting the
        password if matched."""

        pfile = open(self.pgpass,'r')
        lines = pfile.readlines()
        pfile.close()

        for line in lines:
            fields = line.strip().split(':')
            if (fields[0] == self.options.hostname or fields[0] == '*') and \
               (fields[1] == str(self.options.port) or fields[1] == '*') and \
               (fields[2] == self.options.database or fields[2] == '*') and \
               (fields[3] == self.options.username or fields[3] == '*'):
                return fields[4]
        return False

    def connection_string(self, ssl=False):
        """Provides a libpq-compatible connection string. Not comprehensive for
        all options.  Use this with psycopg2, etc."""

        if ssl:
            sslmode = 'enable'
        else:
            sslmode = 'disable'
        if not hasattr(self, 'options'):
            return None 

        constr = \
        "dbname='%s' host='%s' port='%i' user='%s' password='%s' sslmode='%s'"

        return constr % (self.options.database, self.options.hostname, \
                         self.options.port, self.options.username, \
                         self.options.password, sslmode)

    def parse_args(self, args=None, values=None):
        """Extend the default method to allow for pgpass parsing."""

        self.options, self.args = OptionParser.parse_args(self, args=args,
                                                          values=values)
        if self.options.no_password and self.options.force_password:
            self.error("Options %s are mutually exclusive." % \
                repr([self.options.no_password, self.options.force_password]))
        
        # Read in the pgpass file
        if os.path.exists(self.pgpass):
            if system() != 'Windows':
                mode = os.stat(self.pgpass)[stat.ST_MODE]
                if (stat.S_IROTH & mode) or (stat.S_IRGRP & mode):
                    # Bad user, chmod 600 your pgpass
                    print 'WARNING: password file "%s" has world' % self.pgpass + \
                        ' or group read access; permission should be u=rw (0600)'
                else:
                    possible_password = self.__read_pgpass()
                    setattr(self.options, 'password', possible_password)
        else:
            print "Path %s does not exist." % self.pgpass

        # Are we going to prompt for a password?
        if ((hasattr(self.options, 'password') == False or \
             self.options.password == False) and not \
             self.options.no_password) or self.options.force_password:
            try:
                self.options.password = getpass()
            except GetPassWarning:
                pass 
        return (self.options, self.args)

    def __init__(self, usage=None, option_list=None, option_class=Option,
                 version=None, conflict_handler='error', description=None,
                 formatter=None, add_help_option=True, prog=None, epilog=None):
        """Extend the constructor to build standard psql-like options."""

        OptionParser.__init__(self, usage=usage, add_help_option=False,
                              option_list=option_list,
                              option_class=option_class, version=version,
                              conflict_handler=conflict_handler,
                              description=description, formatter=formatter,
                              prog=None, epilog=None)

        # Parse environmental variables, and fallback to very-defaults
        defaults = self.__pg_defaults()

        self.add_option('-H', '--help',
                        action='help',
                        help='show this help message and exit')
        self.add_option('-h', '--host',
                        dest='hostname', metavar='HOSTNAME',
                        default=defaults['PGHOST'],
                        help='database server host (default: %s)' % \
                        defaults['PGHOST'])
        self.add_option('-p', '--port', dest='port', metavar='PORT',
                        default=defaults['PGPORT'], type='int',
                        help='database server port (default: %i)' % \
                        defaults['PGPORT'])
        self.add_option('-U', '--username', dest='username',
                        metavar='USERNAME', default=defaults['PGUSER'],
                        help='database user name (default: "%s")' % \
                        defaults['PGUSER'])
        self.add_option('-w', '--no-password',
                        dest='no_password', action='store_true',
                        help='never prompt for password')
        self.add_option('-W', '--password',
                        dest='force_password', action='store_true',
                        help='force password prompt ' + \
                        '(should happen automatically)')
        self.add_option('-d', '--dbname', dest='database',
                        default=defaults['PGDATABASE'], metavar='DBNAME',
                        help='database name to connect to (default: "%s")' % \
                            defaults['PGDATABASE'])

        # Find our pgpass and store the path for later.
        if os.environ.has_key('PGPASSFILE'):
            self.pgpass = os.environ['PGPASSFILE']
        elif system() == 'Windows':
            self.pgpass = os.environ['APPDATA'] + \
                '\\\\postgresql\\\\pgpass.conf'
        else:
            self.pgpass = os.path.expanduser('~') + '/.pgpass'

