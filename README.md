Bugsplat Tool
=============

[Bugsplat](http://www.bugsplat.com) utility for getting/setting bugsplat information.

* Add and remove users from databases
* Retreive crash entries and summaries as json data

Help
```
usage: bugsplat_tool.py [-h] [-u USER] [-p PASSWORD]
                        [-a ADDUSER [ADDUSER ...]] [-r REMUSER [REMUSER ...]]
                        [-d DBS [DBS ...]] [-t TAGS [TAGS ...]] [-s] [-call]
                        [-csum] [-cver] [-cusr] [-dom DOMAIN] [-c COUNT] [-v]
                        [-o OUT] [-i ID]

Get and set various bugsplat data. Uses json file for database listing and
properties. You can match database by name or tag through this file. Uses
'default' tag if no database or tag supplied with the command. Try
'bugsplat_tool.py -call -u Fred -p Flintstone' to see a demo. Hosted:
https://github.com/RoscoP/bugsplat_tool version: 1.0.0

optional arguments:
  -h, --help            show this help message and exit
  -u USER, --user USER  User name (full e-mail) for bugsplat authentication
  -p PASSWORD, --password PASSWORD
                        Password for bugsplat authentication
  -a ADDUSER [ADDUSER ...], --adduser ADDUSER [ADDUSER ...]
                        Add user to selected databases
  -r REMUSER [REMUSER ...], --remuser REMUSER [REMUSER ...]
                        Del user to selected databases
  -d DBS [DBS ...], --dbs DBS [DBS ...]
                        List of databases to use
  -t TAGS [TAGS ...], --tags TAGS [TAGS ...]
                        Tags to match for database selection
  -s, --show            Show database and tags matched
  -call, --allcrash     Show allcrash information for database selection
  -csum, --summary      Show summary information for database selection
  -cver, --version      Show version information for database selection
  -cusr, --userlist     Show user information for database selection
  -dom DOMAIN, --domain DOMAIN
                        Domain to use for users when adding.
  -c COUNT, --count COUNT
                        Max count of crash/summary info to get
  -v, --verbose         Show detailed logging
  -o OUT, --out OUT     File to output results to, otherwise it goes to stdout
  -i ID, --id ID        Retreive records up to this id
```

Demo: `bugsplat_tool.py -call -u Fred -p Flintstone`


