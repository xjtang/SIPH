""" Module for downloading VIIRS or MODIS product from https server
"""
import os
import sys
import re
import argparse
import glob
try:
    import urllib.request as urllib
except:
    import urllib2 as urllib
try:
    from http.cookiejar import CookieJar as cj
except:
    from cookielib import CookieJar as cj
from calendar import isleap
from datetime import datetime as dt
from ..common import *


_HTTP = 'https://e4ftl01.cr.usgs.gov/'
CHUNK = 1024*1024


def download(url, des, overwrite=False, username='NA', password='NA'):
    """ Download and save a file from ftp

    Args:
      url (str): the link to the file
      des (str): destination to save the file
      overwrite (bool): overwrite or not
      username (str): username
      password (str): password

    Returns:
      0: successful
      1: error due to des
      2: error due to url

    """
    # check if file already exists
    if (not overwrite) and os.path.isfile(des):
        log.warning('{} already exists.'.format(des.split('/')[-1]))
        return 1

    # download file
    try:
        if not username == 'NA' and not password == 'NA':
            pw_manager = urllib.HTTPPasswordMgrWithDefaultRealm()
            pw_manager.add_password(None, "https://urs.earthdata.nasa.gov",
                                        username, password)
            cookie_jar = cj()
            opener = urllib.build_opener(
                urllib.HTTPBasicAuthHandler(pw_manager),
                urllib.HTTPCookieProcessor(cookie_jar))
            urllib.install_opener(opener)
        req = urllib.Request(url)
        response = urllib.urlopen(req)
    except:
        log.error('{}...failed.'.format(url))
        return 2
    else:
        with open(des, 'wb') as f:
            while True:
                data = response.read(CHUNK)
                if not data:
                    break
                else:
                    f.write(data)

    # complete download
    log.info('{}...completed.'.format(url.split('/')[-1]))

    # done
    return 0


def locate_data(url, sensor, collection, product, tile, year, day):
    """ Locate the data file on ftp based on download criteria

    Args:
      url (str): url address for https server
      sensor (str): V for VIIRS, M for MODIS
      collection (int): 5 or 6 for MODIS, 1 for VIIRS
      product (str): which product (e.g. MOD09GA)
      tile (list, int): tile, [h, v]
      year (int): which year
      day (list, int): which day, 0 for all year, [start, stop] for range

    Returns:
      list: list of links to the files
      1: found nothing

    """
    # handle sensor, collection, product and yaer
    if sensor == 'V':
        url = '{}VIIRS/{}.{:03}/'.format(url, product, collection)
    else:
        if product[1] == 'O':
            url = '{}MOLT/{}.{:03}/'.format(url, product, collection)
        elif product[1] == 'Y':
            url = '{}MOLA/{}.{:03}/'.format(url, product, collection)
        else:
            url = '{}MOTA/{}.{:03}/'.format(url, product, collection)

    # handle date tile
    url_list = []
    for i in range(day[0], day[1]+1):
        # read html page
        try:
            _date = doy_to_date(year*1000+i)
            day_string = '{}.{:02}.{:02}'.format(_date[0], _date[1], _date[2])
            link = '{}{}/'.format(url, day_string)
            req = urllib.Request(link)
            response = urllib.urlopen(req)
            page = str(response.read())
        except:
            log.warning('Cannot read {}'.format(link))
            continue

        # search for image name
        pattern = re.compile('{}\.A{}{:03}\.h{:02}v{:02}\.{:03}\..{{13}}\.h5'.format(
                                product, year, i, tile[0], tile[1], collection))
        m = re.search(pattern, page)
        if m:
            url_list.append('{}{}'.format(link, m.group()))
        else:
            log.warning('Find nothing for day {}'.format(i))

    # done
    if len(url_list) == 0:
        log.warning('Found nothing.')
        return 1
    else:
        return url_list


def download_data(url, username, password, des, sensor, collection, product,
                    tile, year, day, update):
    """ Download a set of MODIS or VIIRS data from FTP

    Args:
      url (str): url address for https server
      username (str): username
      password (str): password
      sensor (str): V for VIIRS, M for MODIS
      collection (int): 5 or 6 for MODIS, 1 for VIIRS
      product (str): which product (e.g. MOD09GA)
      tile (list, int): tile, [h, v]
      year (int): which year
      day (list, int): which day, 0 for all yea, [start, stop] for range
      update (bool): update existing image or not

    Returns:
      0: successful
      1: cannot locate files
      2: cannot create output folder

    """
    # locate files
    log.info('Locating files.')
    file_list = locate_data(url, sensor, collection, product, tile, year, day)
    if isinstance(file_list, list):
        n = len(file_list)
        log.info('Found {} files.'.format(n))
    else:
        return 1

    # check output location
    if not os.path.exists(des):
        log.warning('{} does not exist, trying to create one.'.format(des))
        try:
            os.makedirs(des)
        except:
            log.error('Cannot create output folder {}'.format(des))
            return 2

    # download files
    if not des[-1] == '/':
        des = des + '/'
    log.info('Downloading files.')
    count = 0
    for f in file_list:
        # check if old file already exists
        fn = f.split('/')[-1]
        true_fn = fn.split('.')
        del true_fn[-2:]
        true_fn = '.'.join(true_fn)
        old_file = glob.glob('{}{}*.h5'.format(des, true_fn))
        if old_file and not update:
            log.warning('{} old file already exists.'.format(true_fn))
        else:
            if download(f, (des+fn), False, username, password) == 0:
                count += 1
                if old_file and update:
                    for f2 in old_file:
                        os.remove(f2)

    # done
    log.info('Download completed.')
    log.info('Successfully downloaded {}/{} files.'.format(count,n))
    return 0


# download data
if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', action='store', type=str,
                        dest='username', help='Username, required.')
    parser.add_argument('-w', '--password', action='store', type=str,
                        dest='password', help='Password, required.')
    parser.add_argument('-s', '--sensor', action='store', type=str,
                        dest='sensor', default='V',
                        help='V for VIIRS, M for MODIS')
    parser.add_argument('-c', '--collection', action='store', type=int,
                        dest='collection', default=1,
                        help='5 or 6 for MODIS, 1 for VIIRS')
    parser.add_argument('-p', '--product', action='store', type=str,
                        dest='product', default='VNP09GA',
                        help='which product (e.g. MOD09GA)')
    parser.add_argument('-t', '--tile', action='store', type=int, nargs=2,
                        dest='tile', default=[12,9], help='tile, give h and v')
    parser.add_argument('-y','--year', action='store', type=int, dest='year',
                        default=dt.now().year, help='which year')
    parser.add_argument('-d','--day', action='store', type=int, nargs=2,
                        dest='day', default=[0,0],
                        help='which days, give start and stop')
    parser.add_argument('--update', action='store_true',
                        help='update existing image')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # check if arguments and options are valid
    if args.username is None:
        log.error('Missing username.')
        sys.exit(1)
    if args.password is None:
        log.error('Missing password.')
        sys.exit(1)
    if args.sensor == 'V':
        if args.collection != 1:
            log.error('Invalid collection, use 1 for VIIRS.')
            sys.exit(1)
        if args.product not in ['VNP09GA']:
            log.error('Invalid product.')
            sys.exit(1)
    elif args.sensor == 'M':
        if args.platform not in [5, 6]:
            log.error('Invalid collection, use 5 or 6 for MODIS.')
            sys.exit(1)
        if args.product not in ['MOD09GA', 'MYD09GA']:
            log.error('Invalid product.')
            sys.exit(1)
    else:
        log.error('Invalid sensor, use M for MODIS V for VIIRS.')
        sys.exit(1)
    if not 0 <= args.tile[0] <= 35:
        log.error('Invalid tile h, must be between 0 and 35.')
        sys.exit(1)
    if not 0 <= args.tile[1] <= 35:
        log.error('Invalid tile v, must be between 0 and 35.')
        sys.exit(1)
    if all(x == 0 for x in args.day):
        args.day = [1, (366 if isleap(args.year) else 365)]
    if not (args.day[1]>=args.day[0] and
        all(0 < x <= (366 if isleap(args.year) else 365) for x in args.day)):
        log.error('Invalid day range.')
        sys.exit(1)

    # run function to download data
    log.info('Starting to download data...')
    log.info('Searching for {}.{}.{}.h{:02}v{:02}.{}.{}.{}'.format(args.sensor,
                args.collection,args.product,args.tile[0], args.tile[1],
                args.year,args.day[0],args.day[1]))
    log.info('From {}'.format(_HTTP))
    log.info('Saving in {}'.format(args.des))
    download_data(_HTTP, args.username, args.password, args.des, args.sensor,
                    args.collection, args.product, args.tile, args.year,
                    args.day, args.update)
