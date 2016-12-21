# cdpcrawler

Script uses ssh and telnet to crawl a network and display cdp neighbor information.  This information is parsed and the neighbors are connected to and so on.

```
Usage: cdpscanner.py [Options]
  Note: All options are optional.  User is prompted or defaults are used.
  -h or --help:  This help screen
  -i or --inputfile: specifies a file containing hosts to connect to.
  -u or --username: specifies a username to use
  -p or --password: Specifies the password to use
  -v or --verbose: Enables verbose output
  -t or --telnet:  Enables fallback to telnet
  -o or --output:  Prints the inventory of all of the devices at the end
  -H or --hosts:  specifies hosts via comma seperated values
  -T or --threads:  specifices the number of threads (defaults to 8)
  -g or --graph:  enables graphing of the network and specifices the output file
```

## Project dependancies:

### netmiko 
* https://github.com/ktbyers/netmiko
* `pip install netmiko`

### openpyxl 
* https://openpyxl.readthedocs.io/en/default/#
* `pip install openpyxl`

## Graphing function also requires

### pydot 
* https://pypi.python.org/pypi/pydot
* `pip install pydot`

### Graphviz
* http://www.graphviz.org/Download.php







