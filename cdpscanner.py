import os
try:
    from netmiko import ConnectHandler
except:
    print '[!] Looks like you are missing the paramiko library.  run \'pip install netmiko\''
    if os.name == 'nt':
        print '[!] *NOTE* you must install the Microsoft Visual C++ Compiler for Python 2.7 ' \
              'before installing paramiko.\r\n'\
              'This can be found at http://www.microsoft.com/en-us/download/details.aspx?id=44266'
import getopt
import sys
import re
import glob
import getpass
import socket
from openpyxl import Workbook

#help message
def helpmsg():
    print 'Usage: cdpscanner.py [Options] <IP address or Host(optional)>' \
          '  Note: All options are optional.  User is prompted or defaults are used.' \
          '  -h or --help:  This help screen\n' \
          '  -i or --inputfile: specifies a file containing hosts to connect to.\n' \
          '  -u or --username: specifies a username to use\n' \
          '  -p or --password: Specifies the password to use\n' \
          '  -c or --commands: Specifies a list of commands to send\n' \
          '  -v or --verbose: Enables verbose output\n'\
          '  -t or --telnet:  Enables fallback to telnet\n'\
          '  -d or --directory: Specifies a a directory to place the output files into\n'\
          '  --inventory:  Prints the inventory of all of the devices at the end\n'\
          '  -o or --output:  Prints the inventory of all of the devices at the end\n'\
          '  -H or --hosts:  specifies hosts via comma seperated values\n'




def getinfo(username, password, host, commands, mode):
    all_output = []
    row = []
    if mode == "SSH":
        device = {
            'device_type': 'cisco_ios',
            'ip'         : host,
            'username'   : username,
            'password'   : password,
            'port'       : 22,  # optional, defaults to 22
            'secret'     : '',  # optional, defaults to ''
            'verbose'    : False,  # optional, defaults to False
        }
    elif mode == "Telnet":
        device = {
            'device_type': 'cisco_ios_telnet',
            'ip'         : host,
            'username'   : username,
            'password'   : password,
            'port'       : 23,  # optional, defaults to 22
            'secret'     : '',  # optional, defaults to ''
            'verbose'    : False,  # optional, defaults to False
        }
    print('Connecting to %s with %s' % (host,mode) )
    # Create instance of SSHClient object
    net_connect = ConnectHandler(**device)
    # Automatically add untrusted hosts (make sure okay for security policy in your environment)
    print('%s connection established to %s' % (mode,host))
    # Use invoke_shell to establish an 'interactive session'
    a = re.search(r'(.*)#',net_connect.find_prompt())
    if a is not None:
        hostname = a.group(1)
    else:
        hostname = host
    for command in commands:
        output = net_connect.send_command(command)
        all_output.append(output)
        if command == 'show inventory':
            lines = output.split('\n\n')
            for line in lines:
                new_line = line.replace('\n','')
                a = re.search(r'NAME:\ ?(\S+).*PID:\ ?(\S+).*SN:\ ?(\S+)',new_line)
                if a is not None:
                    pid = a.group(2)
                    serial = a.group(3)
                    row.append([hostname,pid,serial])
        if verbose_mode:
            print(output)
    return all_output, row

def find_hosts_from_output(output):
    neighbor_list = []
    global host_set
    global seen_before
    cdp_regex = re.compile(r'\ *(\S+)(?:[^\r\n]*\r?\n){1,4}[\ ]*IP(?:v4)* [aA]ddress:\ (\S+)\r?\nPlatform: (?:cisco )*(\S+),[\ ]*Capabilities:.*(Switch)')
    for item in output:
        split_output = item.split('Device ID:')
        for single_device in split_output:
            matches = re.findall(cdp_regex,single_device)
            for match in matches:
                if match[1] not in seen_before:
                    host_set.add(match[1])
                    seen_before.add(match[1])
                neighbor_list.append([match[0],match[1],match[2]])
    return neighbor_list


#Declaration of global variables
inputfile = None
host_set = set()
username = ''
password = ''
failed_hosts = set()
TIMEOUT = 30
org_dir = os.curdir
working_directory = os.curdir
verbose_mode = False
telnet_enabled = False
current_set = set(host_set)
seen_before = set()
device = []
inventory = []
inventory_enabled = False
failed_telnet = []
failed_ssh = []
outputfile = 'output.xlsx'
# Default commamnds if no additional commands are specififed in the CLI arguments
commands = ['show cdp neighbor detail',
            'show inventory']

#setup excel workbook for output
wb = Workbook()
inventory_ws = wb.active
inventory_ws.title = u'Inventory'
neighbor_ws = wb.create_sheet("Neighbors")
errors_ws = wb.create_sheet("Errors")
#Add headers to worksheets
inventory_ws.append(['Hostname', 'Device Model', 'Serial Number'])
neighbor_ws.append(['Hostname', 'Neighbor Hostname', 'Neighbor IP', 'Neighbor Model'])
errors_ws.append(['Hostname', 'Error', 'Protocol'])



# Run CLI parser function to set variables altered from defaults by CLI arguments.
try:
    opts, args = getopt.getopt(sys.argv[1:],"i:u:p:hd:vtH:o:",
                               ["input=", "user=", "password=","directory=","verbose","telnet",
                                "inventory","hosts=","output="])
except getopt.GetoptError:
    helpmsg()
    sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        helpmsg()
        sys.exit()
    elif opt in ('-i', '--input'):
        inputfile = arg
        with open(org_dir+'/'+inputfile, 'rb') as hostfile:
            for device in hostfile:
                try:
                    socket.inet_aton(device.rstrip('\r\n'))
                    host_set.add(device.rstrip('\r\n'))
                except:
                    try:
                        ip_from_host = socket.gethostbyname(device.rstrip('\r\n'))
                        host_set.add(ip_from_host)
                    except:
                        print("%s is not a valid host name or IP address" % device)
                        sys.exit(2)
    elif opt in ('-t', '--telnet'):
        telnet_enabled = True
    elif opt in ('-v', '--verbose'):
        verbose_mode = True
    elif opt in ('-o', '--output'):
        outputfile = arg
    elif opt in ('-u', '--user'):
        username = arg
    elif opt in ('-p', '--password'):
        password = arg
    elif opt in ('-H', '--hosts'):
        for i in arg.split(','):
            host_set.add(i)
    elif opt in ('--inventory'):
        inventory_enabled = True
for opt, arg in opts:
    if opt in ('-d', '--directory'):
        working_directory = arg
        try:
            os.chdir(working_directory)
        except Exception as e:
            helpmsg()
            print(e)
            sys.exit()
for arg in args:
    try:
        socket.inet_aton(arg)
        host_set.add(arg)
    except:
        try:
            ip_from_host = socket.gethostbyname(arg)
            host_set.add(ip_from_host)
        except:
            print("%s is not a valid host name or IP address" % arg)
            sys.exit(2)
#Set list of IP addreses to connect to if the -i input file is not used
if host_set == []:
    host_set.append(raw_input("Enter Switch Hostname or IP Address: ").upper())
if username == '':
    username = raw_input("Enter Username: ")
if password == '':
     password = getpass.getpass()

# Create a working copy of the set that contains all of the hosts.

# Create a loop to make crawler recursive
while host_set != set([]):
    # iterate through the set of hosts
    for host in current_set:
            # remove the host you are going to connect to from the set.
        currenthost = host_set.pop()
        device_output = ''
        try:
            # Try SSH and if that fails try telnet.
            device_output, inventory_rows = getinfo(username, password, currenthost, commands,'SSH')
            for row in inventory_rows:
                inventory_ws.append(row)
            # Check output for new hostnames
        except Exception as e:
            print("SSH connection to %s failed" % host)
            print(e)
            failed_ssh.append(host)
            errors_ws.append([host, unicode(e),'SSH'])
            if telnet_enabled:
                try:
                    device_output, inventory_rows = getinfo(username, password, currenthost, commands, 'Telnet')
                except Exception as e:
                    print "telnet connection to %s failed" % host
                    failed_telnet.append(host)
                    errors_ws.append([host, unicode(e), 'telnet'])
            else:
                pass
        finally:
            neighbor_list = find_hosts_from_output(device_output)
            for neighbor in neighbor_list:
                neighbor_ws.append([host,neighbor[0],neighbor[1],neighbor[2]])

    # Update the current list with the most recent updated host_set.
    current_set = set(host_set)

#After everything has been completed or removed
if inventory_enabled == True:
    devices = glob.glob('*.txt')
    for device in devices:
        with open(device) as dfile:
            for line in dfile:
                matches = re.findall(r'PID:\ *(\S+),.*SN:(\S+)',line)
                if matches != []:
                    inventory.append([host,matches[0],matches[1]])


for line in failed_hosts:
    print '[!] %s failed both ssh and telnet' % line
wb.save(outputfile)