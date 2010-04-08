from optparse import * 
from platform import system
from getpass import getpass, getuser, GetPassWarning
import os 



class PGOptionParser(OptionParser):
    """PGOptParser is OptionParser, except it provides automatic configuration to read psql-like options for mucking with PostgreSQL databases.  It'll even read from pgpass!"""

    def read_pgpass(self):
        """Read the file located in self.pgpass and parse it, setting the password if matched."""
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
        """Provides a libpq-compatible connection string. Not comprehensive for all options.  Use this with psycopg2, etc."""
        if ssl:
            sslmode = 'enable'
        else:
            sslmode = 'disable'
        if not hasattr(self, 'options'):
            return None 

        constr = "dbname='%s' host='%s' port='%i' user='%s' password='%s' sslmode='%s'"
        return constr % (self.options.database, self.options.hostname, \
                         self.options.port, self.options.username, \
                         self.options.password, sslmode)
            

    def parse_args(self, args=None, values=None):
        """Override the default method so we can do our own checks."""
        self.options, self.args = OptionParser.parse_args(self, args=args, values=values)
   
        if self.options.no_password and self.options.force_password:
            self.error("Options %s are mutually exclusive." % repr([self.options.no_password, self.options.force_password]))

        if os.path.exists(self.pgpass):
            possible_password = self.read_pgpass()
            setattr(self.options, 'password', possible_password)

        if ((hasattr(self.options, 'password') == False or self.options.password == False) and not self.options.no_password) \
            or self.options.force_password:
            try:
                self.options.password = getpass()
            except GetPassWarning:
                pass 
        return (self.options, self.args)
            

    def __init__(self, usage=None, option_list=None, option_class=Option, version=None, conflict_handler='error', description=None, formatter=None, add_help_option=True, prog=None, epilog=None):
        """Override the default constructor to build standard psql-like options."""
        OptionParser.__init__(self, usage=usage, add_help_option=False, option_list=option_list, option_class=option_class, version=version, conflict_handler=conflict_handler, description=description, formatter=formatter, prog=None, epilog=None)
        
        self.add_option('-H', '--help',
                        action='help',
                        help='show this help message and exit')
        self.add_option('-h', '--host',
                        dest='hostname', metavar='HOSTNAME', default='localhost',
                        help='database server host (default: localhost)')
        self.add_option('-p', '--port',
                        dest='port', metavar='PORT', default=5432, type='int',
                        help='database server port (default: 5432)')
        self.add_option('-U', '--username',
                        dest='username', metavar='USERNAME', default=getuser(),
                        help='database user name (default: "%s")' % getuser())
        self.add_option('-w', '--no-password',
                        dest='no_password', action='store_true',
                        help='never prompt for password')
        self.add_option('-W', '--password',
                        dest='force_password', action='store_true',
                        help='force password prompt (should happen automatically)')
        self.add_option('-d', '--dbname',
                        dest='database', default=getuser(), metavar='DBNAME',
                        help='database name to connect to (default: "%s")' % getuser())

        # Find our pgpass and store the path for later.
        if system() == 'Linux':
            self.pgpass = os.path.expanduser('~') + '/.pgpass'
        elif system() == 'Windows':
            self.pgpass = os.environ['APPDATA'] + '\\\\postgresql\\\\pgpass.conf'
