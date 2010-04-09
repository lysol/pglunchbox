import os
import stat
from optparse import * 
from platform import system
from getpass import getpass, getuser, GetPassWarning


class PermissionWarning(Warning):

    def __init__(self, filename):
        self.filename = filename

    def __str__(self):
        return 'WARNING: password file "%s" has world or group' % self.pgpass + \
            ' read access; permission should be u=rw (0600)'
    

class PGPassFile:

    def __read_pgpass(self, filename):
        """Read the file located in self.pgpass and parse it, setting the
        password if matched."""

        pfile = open(filename,'r')
        self.pgpass_lines = [line.strip().split(':') for line in \
            pfile.readlines()]
        pfile.close()

    def __item_match(self, input, mask):
        """Helper function for our map functions."""

        if input == mask:
            return True
        elif mask == '*':
            return True
        else:
            return False


    def get_items(self):
        """Return a nice list of dicts for pgpass lines."""

        return [{'hostname': line[0], 'port': line[1], 'database': line[2],
            'username': line[3], 'password': line[4]} for line in \
            self.pgpass_lines]

    def get_login(self, **kwargs):
        """Parse the stored pgpass lines and return a tuple containing a \
        username and password."""

        for fields in self.pgpass_lines:
            field_list = ['hostname', 'port', 'database']
            settings_list = []
            for field in field_list:
                if kwargs.has_key(field):
                    settings_list.append(kwargs[field])
                else:
                    settings_list.append(None)
            matches = map(lambda x: self.__item_match(str(settings_list[x]), \
                str(fields[x])), range(3))
            if matches == [True, True, True]:
                return (fields[3], fields[4])
        return None

    def get_password(self, **kwargs):
        """Parse the stored pgpass lines and return the password."""
    
        for fields in self.pgpass_lines:
            field_list = ['hostname', 'port', 'database', 'username']

            settings_list = []
            for field in field_list:
                if kwargs.has_key(field):
                    settings_list.append(kwargs[field])
                else:
                    settings_list.append(None)
            
            matches = map(lambda x: self.__item_match(str(settings_list[x]), \
                str(fields[x])), range(4))
            if matches == [True, True, True, True]:
                return fields[4]
        return None

    def __init__(self, filename=''):
        """Populate the pgpass lines."""

        if filename == '':
            # Find our pgpass and store the path for later.
            if os.environ.has_key('PGPASSFILE'):
                filename = os.environ['PGPASSFILE']
            elif system() == 'Windows':
                filename = os.environ['APPDATA'] + \
                    '\\\\postgresql\\\\pgpass.conf'
            else:
                filename = os.path.expanduser('~') + '/.pgpass'       

        # Read in the pgpass file
        if os.path.exists(filename):
            if system() != 'Windows':
                # !Windows.  Check permissions.
                mode = os.stat(filename)[stat.ST_MODE]
                if (stat.S_IROTH & mode) or (stat.S_IRGRP & mode):
                    # Bad user, chmod 600 your pgpass
                    raise PermissionWarning(filename)
                else:
                    self.__read_pgpass(filename)
                    # possible_password = self.__read_pgpass()
                    # setattr(self.options, 'password', possible_password)
            else:
                # Windows user.  No permissions check.
                self.__read_pgpass(filename)
        else:
            # Gracefully fall back.
            self.pgpass_lines = []


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
        
        pgpass = PGPassFile()
        kwargs = {}
        
        for key in ['hostname', 'port', 'database', 'username']:
            if hasattr(self.options, key):
                kwargs[key] = getattr(self.options, key)
       
        possible_password = pgpass.get_password(**kwargs)
        if possible_password != None:
            setattr(self.options, 'password', possible_password)

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
