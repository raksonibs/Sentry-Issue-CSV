import os
import sys
import logging
import traceback
import csv

# Third party module, not installed with python. Needs to be installed with virtualenv + pip
import requests


def fetchUrl(url, authToken):
    '''Fetch a url and deal with authentication using an authToken'''

    try:
        s = requests.Session()
        r = s.get(url, headers={'Authorization': 'Bearer {}'.format(authToken)})
        r.raise_for_status()
        return True, r

    except requests.exceptions.RequestException:
        msg = traceback.format_exc()
        msg = 'Request error: {}'.format(msg)
        logging.fatal(msg)
        return False, None


def mkRow(event):
    # Here you can use the python debugger to inspect events
    # print event.keys()
    # import pdb; pdb.set_trace()

    row = {}
    # user_id, ts, device, device_family, os, release, version

    userInfo = event['user']
    userId = userInfo['data'].get('userid', 'n/a')
    row['userid'] = userId

    # If a better way to print time is needed, use this 
    # format "%Y-%m-%d %H:%M:%S" for excel when printing time,
    # after parsing from dateCreated
    row['timestamp'] = event['dateCreated']

    # (Pdb) event['contexts']['device']
    '''
      {u'model_id': u'D101AP', 
       u'family': u'iPhone', 
       u'simulator': False, 
       u'network_operator': u'AT&T', 
       u'architecture': u'64-bit', 
       u'model': u'iPhone9,3', 
       u'type': u'device'}
    '''
    deviceInfo = event['contexts']['device']
    row['device_family'] = deviceInfo.get('family', 'n/a')
    row['device_model'] = deviceInfo.get('model', 'n/a')
    row['device_model_id'] = deviceInfo.get('model_id', 'n/a')

    # OS
    '''
    (Pdb) event['contexts']['os']
    {u'kernel_version': u'n/a', 
     u'version': u'10.3.2', 
     u'type': u'os', 
     u'name': u'iOS', 
     u'build': u'14F89'}
    '''
    row['os_name'] = event['contexts']['os'].get('name', 'n/a')
    row['os_version'] = event['contexts']['os'].get('version', 'n/a')

    # parse tags
    tags = {}
    for item in event['tags']:
        key = item['key']
        value = item['value']
        tags[key] = value

    release = tags['release']
    version = tags['version']

    row['release'] = release
    row['version'] = version

    return row


def processEvents(url, output_path):
    '''Process all events for an issue and do something fun with it'''

    authToken = 'XXXX_YOUR_AUTH_TOKEN_XXXX'

    with open(output_path, 'w') as csvfile:
        fieldnames = [
            'userid', 
            'timestamp', 
            'device_family',
            'device_model',
            'device_model_id',
            'os_name',
            'os_version',
            'release', 
            'version'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        while True:
            print 'fetching', url
            ok, r = fetchUrl(url, authToken)
            events = r.json()
            print 'retrieved {} events'.format(len(events))

            if len(events) == 0:
                break

            hasNext = r.links.get('next')
            if hasNext is None:
                break

            url = r.links['next']['url']

            for event in events:
                writer.writerow(mkRow(event))


if __name__ == '__main__':
    # Script input
    
    # 1. A url to the crash
    # https://getsentry.io/sentry/a_project_name/issues/5163217

    url = 'https://getsentry.io/api/0/issues/5163217/events/'

    # 2. The output csv file
    output_path = 'out.csv'

    processEvents(url, output_path)