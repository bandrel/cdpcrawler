import glob
import re
import getopt
import sys
import os

verbose = False
directory = ''
site = ''

def print_help():
    print 'findinscope.py -d <directory> (optional)'
try:
    opts, args = getopt.getopt(sys.argv[1:],"hd:s:v",["help", "directory=", 'site=','verbose'])
except getopt.GetoptError:
    print_help()
    sys.exit(2)

for opt, arg in opts:
    if opt == '-h':
        print_help()
        sys.exit()
    elif opt in ('-d', '--directory'):
        directory = arg
    elif opt in ('-v', '--verbose'):
        verbose = True
    elif opt in ('-s', '--site'):
        site = arg


if directory is not '':
    try:
        os.chdir(directory)
    except Exception as e:
        print_help()
        print e
        sys.exit()

hostnames = []
for file in glob.glob('*.txt'):
    host = ''
    with open(file) as switch_output:
        for line in switch_output:
            h = re.search(r'^(\S+)[#>]',line)
            s = re.search(r'(WS-C\S+).*SN: (\S+)',line)
            if h is not None:
                host = h.group(1)
            if s is not None:
                hostnames.append(host+'\t'+s.group(1)+'\t'+s.group(2))

host_set = set(hostnames)
if site is '':
    for hostname in host_set:
        print hostname

else:
    for hostname in host_set:
        sitecode = hostname[0:3]
        if sitecode.upper() == site.upper():
            print hostname



