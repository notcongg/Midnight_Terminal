import getpass
username = getpass.getuser()
def cmd_whoami(args):
    print(username)