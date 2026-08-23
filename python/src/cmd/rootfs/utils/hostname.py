import socket
hostname = socket.gethostname()
def cmd_hostname(args):
    print(hostname)