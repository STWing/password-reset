#!/usr/bin/python

# https://docs.python.org/2/library/cgi.html
import cgi
import cgitb
import os
import ldap
#cgitb.enable()  # enable debug logging - TODO: comment this out

def print_file(filename):
    with open(filename, 'r') as f:
        print f.read(),

# Not needed. LDAP server is doing the hashing for us.
#def make_secret(password):
#    h = sha512_crypt.encrypt(password, rounds=65536)
#    return '{CRYPT}' + h

def main():
    if os.environ["REQUEST_SCHEME"] != 'https':
        return "Request not made over HTTPS; this shouldn't be possible. Please contact " \
            "<a href='mailto:sysadmin@stwing.upenn.edu'>sysadmin@stwing.upenn.edu</a>."
    if os.environ["SCRIPT_URI"] != "https://www.stwing.upenn.edu/pw/":
        return "This isn't the right URL. Please go to " \
            "<a href='https://www.stwing.upenn.edu/pw/'>https://www.stwing.upenn.edu/pw/</a>."

    form = cgi.FieldStorage()

    username = form.getfirst('username')
    if username == None:
        # the form has not been submitted
        print_file('../form.html')
        return None
    dn = 'uid={},ou=People,dc=stwing,dc=upenn,dc=edu'.format(username)

    oldpw = form.getfirst('password')
    if oldpw == None or len(oldpw) < 1:
        return 'Old password not provided.'

    newpw = form.getfirst('newpw1')
    newpw2 = form.getfirst('newpw2')
    if newpw2 == None or newpw != newpw2:
        return 'New passwords do not match.'
    if newpw == None or len(newpw) < 8:
        return 'Password too short: must be at least 8 characters.'
    if len(newpw) > 255:
        return 'Password too long: must be no more than 255 characters.'

    ld = ldap.initialize('ldap://ldap.lan')
    ld.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
    ld.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
    try:
        res = ld.simple_bind_s(dn, oldpw)
    except Exception:
        return 'Failed to bind to LDAP server. Incorrect username/password?'
    if res[0] != 97:  # 97 = success
        return 'Failed to bind to LDAP server. Incorrect username/password?'

    ld.passwd_s(dn, None, newpw)
    print 'Your password has been reset. Please verify by logging into any STWing service.'
    return

if __name__ == '__main__':
    print "Content-Type: text/html"
    print
    print_file('../header.html')
    ret = main()
    if ret != None:
        print '<p><strong>Error:</strong> {}</p>'.format(ret)
        print_file('../form.html')
    print_file('../footer.html')
