import argparse
import requests
import json
import getpass
import logging
import os
import time

def login(user, passwd):
    log = logging.getLogger('bugsplat')
    log.debug("Logging into bugsplat as user {}".format(user))
    s = requests.Session()
    bs_login = 'https://www.bugsplat.com/login'
    login_info = {'currusername':user, 'currpasswd':passwd}

    r1 = s.get(bs_login)
    r1.raise_for_status()
    r2 = s.post(bs_login, data=login_info)
    r2.raise_for_status()
    log.debug("Login complete")

    return s

def get_data(op, session, dbs, count, ids, baseurl=None, urlargs=None):
    log = logging.getLogger('bugsplat')
    maxpagesize = 1000
    data = []
    # Bugsplat limits count to 1000, if you want more, we have to get it via paging
    pagecount = 1
    if count > maxpagesize:
        pagecount = (int(count)+999) / maxpagesize
        count = maxpagesize

    baseurl = baseurl if baseurl else 'https://www.bugsplat.com/{}/?data&database={{}}&pagesize={{}}&pagenum={{}}{}'.format(op, ('&' + urlargs) if urlargs else '')

    for i, db in enumerate(dbs):
        t1 = time.time()
        dbdata = None
        log.debug("Gathering {} data for database {:30}     : {:>6} entries max".format(op, db, count*pagecount))
        for p in range(pagecount):
            log.debug("Gathering {} data for database {:30} page: {:>6} / {:>6}".format(op, db, p+1, pagecount))
            url = baseurl.format(db, count, p)
            calldata = None

            try:
                r = None
                log.debug("URL: {}".format(url))
                r = session.get(url)
                r.raise_for_status()
                calldata = r.json()
            except Exception as e:
                log.error("Error getting data at url: {} - assuming no more data: {}".format(url, e))
                break

            breakout = 0
            # retreive up to this id
            if ids and i < len(ids):
                if len(calldata[0]['Rows']):
                    log.debug("ID: {} -> {}".format(calldata[0]['Rows'][-1]['id'], calldata[0]['Rows'][0]['id']))
                for j, d in enumerate(calldata[0]['Rows']):
                    if d['id'] == ids[i]:
                        calldata[0]['Rows'] = calldata[0]['Rows'][0:j]
                        breakout = ids[i]
                        break

            # Collect all the multiple pages for the same database together
            if not dbdata:
                dbdata = calldata
            else:
                dbdatalen = len(dbdata[0]['Rows'])
                # Look through the end of the list for duplicates, since the bugsplat database is updating in real time, our pages
                # will not have the correct boarders, and contain duplicates.
                for k in range(min(dbdatalen,100)):
                    if dbdata[0]['Rows'][dbdatalen-1 - k] == calldata[0]['Rows'][0]:
                        dbdata[0]['Rows'] = dbdata[0]['Rows'][:(dbdatalen-1 - k)]
                        break
                dbdata[0]['Rows'] += calldata[0]['Rows']
            if breakout:
                log.debug("Found id {}, stopping after {} records".format(breakout, len(dbdata[0]['Rows'])))
                break

        data += dbdata
        t2 = time.time()
        log.debug("Gathering {} data for database {:30} done: {:>6.3f}".format(op, db, t2-t1))

    return data

def get_email(user, domain):
    return "{}@{}".format(user, domain) if domain else user

def main():
    parser = argparse.ArgumentParser(description="Get and set various bugsplat data.  Uses json file for database listing and properties.  You can match database by name or tag through this file.  Uses 'default' tag if no database or tag supplied with the command.  Try 'bugsplat_tool.py -call -u Fred -p Flintstone' to see a demo.  Hosted: https://github.com/RoscoP/bugsplat_tool")
    parser.add_argument("-u", "--user",         default='',                         help='User name (full e-mail) for bugsplat authentication')
    parser.add_argument("-p", "--password",     default='',                         help='Password for bugsplat authentication')
    parser.add_argument("-a", "--adduser",      default=[], nargs = '+', type=str,  help='Add user to selected databases')
    parser.add_argument("-r", "--remuser",      default=[], nargs = '+', type=str,  help='Del user to selected databases')
    parser.add_argument("-d", "--dbs",          default=[], nargs = '+', type=str,  help='List of databases to use')
    parser.add_argument("-t", "--tags",         default=[], nargs = '+', type=str,  help='Tags to match for database selection')
    parser.add_argument("-O", "--ortag",        action='store_true',                help="Tags are or'd for matching")
    parser.add_argument("-s", "--show",         action='store_true',                help='Show database and tags matched')
    parser.add_argument("-call", "--allcrash",  action='store_true',                help='Show allcrash information for database selection')
    parser.add_argument("-csum", "--summary",   action='store_true',                help='Show summary information for database selection')
    parser.add_argument("-cver", "--version",   action='store_true',                help='Show version information for database selection')
    parser.add_argument("-cusr", "--userlist",  action='store_true',                help='Show user information for database selection')
    parser.add_argument("-czip", "--zips",      action='store_true',                help='Download zips for crashes - works with --allcrash and --keycrash')
    parser.add_argument("-ckey", "--keycrash",  default=None,                       help='Get json for a specific crash ID')
    parser.add_argument("-dom", "--domain",     default='',                         help='Domain to use for users when adding.')
    parser.add_argument("-c", "--count",        default=10,                         help='Max count of crash/summary info to get')
    parser.add_argument("-v", "--verbose",      action='store_true',                help='Show detailed logging')
    parser.add_argument("-o", "--out",          default='',                         help='File to output results to, otherwise it goes to stdout')
    parser.add_argument("-i", "--ids",          default=[], nargs = '+', type=str,  help='Retreive records up to this id, id for each db passed in')
    args = parser.parse_args()

    data = bugsplat_tool(**vars(args))

def bugsplat_tool(  user        = '',
                    password    = '',
                    adduser     = [],
                    remuser     = [],
                    dbs         = [],
                    tags        = [],
                    ortag       = False,
                    show        = False,
                    allcrash    = False,
                    summary     = False,
                    version     = False,
                    userlist    = False,
                    zips        = False,
                    keycrash    = False,
                    domain      = '',
                    count       = 10,
                    verbose     = False,
                    out         = '',
                    return_data = False,
                    ids         = []):

    logging.basicConfig(level=logging.ERROR, datefmt='%Y-%m-%d %H:%M:%S', format='%(message)s')
    log = logging.getLogger('bugsplat')
    log.setLevel(logging.DEBUG)

    is_command = allcrash or summary or version or userlist or zips or keycrash
    if not verbose:
        log.setLevel(logging.INFO)

    with open(os.path.splitext(__file__)[0] + '.json', 'r') as f:
        settings = json.load(f)
        settings_dbs = settings['databases']
        domain = settings.get('domain', domain)

    # if no databases picked, then choose the default set
    if not dbs and not tags:
        tags = ['default']
    # Pick the tagged databases
    if tags:
        if ortag:
            dbs += [db for db in settings_dbs.keys() if set(tags).intersection(set(settings_dbs[db]))]
        else:
            dbs += [db for db in settings_dbs.keys() if set(tags).issubset(set(settings_dbs[db]))]

    if show:
        log.info("{:40} : {}".format('Database', 'Tags'))
        log.info("{:40}---{}".format('-'*40, '-'*30))
        for db in dbs:
            log.info("{:40} : {}".format(db, ", ".join(settings_dbs[db])))
        return

    if not dbs:
        log.warn("No databases selected, nothing to do")
        return
    while not user:
        user = raw_input("Enter in bugsplat user: ")
    while not password:
        password = getpass.getpass("Enter in bugsplat password for {}: ".format(user))

    s = login(user, password)

    # restricted users
    # www.bugsplat.com/users/?update&uId={user-id}&Restricted={true or false}
    if adduser:
        for db in dbs:
            for user in adduser:
                log.debug("Adding user {} to {}".format(user, db))
                r = s.get('https://www.bugsplat.com/users/?insert=true&username={}&database={}'.format(get_email(user, domain).replace('@','%40'), db))
                r.raise_for_status()
                # Bugsplat just says '1' when it successful
                if r.text != '1':
                    log.error("Failed to add user {}, bugsplat returned:\n{}".format(user, r.text.encode('ascii','ignore')[:500]))
    elif remuser:
        full_usernames = [get_email(user, domain) for user in remuser]
        for db in dbs:
            r = s.get('https://www.bugsplat.com/users/?data&database={}&pagesize=1000'.format(db))
            r.raise_for_status()
            uid_table = r.json()
            uids = [{'uid':uid['uId'], 'user':uid['username'].split('@')[0]} for uid in uid_table[0]['Rows'] if uid['username'] in full_usernames]
            for uid in uids:
                log.debug("Deleting user {} uid:{} from {}".format(uid['user'], uid['uid'], db))
                r = s.get('https://www.bugsplat.com/users/?delete&uId={}&database={}'.format(uid['uid'], db))
                r.raise_for_status()
                # Bugsplat just says '1' when it is successful
                if r.text != '1':
                    log.error("Failed to add user {}, bugsplat returned:\n{}".format(user, r.text.encode('ascii','ignore')[:500]))
    elif is_command:
        data = []
        if userlist:
            data = get_data('users', s, dbs, count, ids)
        elif allcrash:
            data = get_data('allCrash', s, dbs, count, ids)
        elif summary:
            data = get_data('summary', s, dbs, count, ids)
        elif version:
            data = get_data('versions', s, dbs, count, ids)
        elif keycrash:
            data = get_data('keycrash', s, dbs, count, ids, urlargs='stackKeyId={}'.format(keycrash))

        if zips and (keycrash or allcrash):
            for d in data[0]['Rows']:
                try:
                    crash_url = "https://www.bugsplat.com/individualCrash/?data&id={}&database={}".format(d['id'], data[0]['Database'])
                    crash_resp = s.get(crash_url)
                    crash_resp.raise_for_status()
                    zip_url = crash_resp.json()['s3URL']
                    zip_resp = s.get(zip_url, stream=True)
                    zip_resp.raise_for_status()
                    zipname = '{}_{}.zip'.format(data[0]['Database'], d['id'])
                    log.info("Saving file: {}".format(zipname))
                    with open(zipname, 'wb') as f:
                        for blk in zip_resp.iter_content(10*1024):
                            f.write(blk)
                except Exception as e:
                    log.error("Failed while trying to save zip for ID: {} - {}".format(d['id'], str(e)))

        if data:
            if return_data:
                return data

            log.debug("Converting data to json text")
            data_str = json.dumps(data, indent=4)
            if out:
                log.debug("Writing data to file: {}".format(out))
                with open(out, "w") as f:
                    f.write(data_str)
            elif not zips:
                log.info(data_str)
    else:
        log.error("Unknown command")

    return None

if __name__ == "__main__":
    main()
