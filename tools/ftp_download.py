""" Module for downloading VIIRS or MODIS product from ftp
"""
import os
import sys
import re
import argparse
from calendar import isleap
from ftplib import FTP
from datetime import datetime as dt

try:
    from ..common.logger import log
except:
    import logging
    log_format = '|%(asctime)s|%(levelname)s|%(module)s|%(lineno)s||%(message)s'
    log_formatter = logging.Formatter(log_format,'%Y-%m-%d %H:%M:%S')
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(log_formatter)
    log_handler.setLevel(logging.INFO)
    log = logging.getLogger(__name__)
    log.addHandler(log_handler)
    log.setLevel(logging.INFO)

_FTP = 'ftp://ladsweb.nascom.nasa.gov/'


def get_ftp(url):
    """ connect to ftp given address

    Args:
      url (str): ftp address

    Returns:
      ftp (FTP): ftp object
      1: ftp connect error
      2: error while moving to folder

    """

    # parse url
    url_split = url.split('://')[-1].split('/')

    # connect to ftp
    try:
        ftp = FTP(url_split[0])
        ftp.login('anonymous','xjtang@bu.edu')
    except:
        log.error('Cannot connect to ftp://{}/'.format(url_split[0]))
        return 1

    # move to folder
    n = len(url_split)
    if n > 1:
        for i in range(1,n):
            try:
                ftp.cwd(url_split[i])
            except:
                log.error('Cannot move to folder {}'.format(url_split[i]))
                return 2

    # done
    return ftp


def locate_data(ftp, sensor, collection, product, tile, year, day):
    """ Locate the data file on ftp based on download criteria

    Args:
      ftp (str or FTP): FTP address or FTP object
      sensor (str): V for VIIRS, M for MODIS
      collection (int): 5 or 6 for MODIS, 1 for VIIRS
      product (str): which product (e.g. MOD09GA)
      tile (list, int): tile, [h, v]
      year (int): which year
      day (list, int): which day, 0 for all year, [start, stop] for range

    Returns:
      list: list of links to the files
      1: found nothing
      2: error due to ftp connection

    """
    # connect to ftp
    if not isinstance(ftp, FTP):
        ftp = get_ftp(ftp)
        if isinstance(ftp, int):
            return 2

    # handle sensor, collection, product and yaer
    url = 'ftp://{}/'.format(ftp.host)
    if sensor == 'V':
        ftp.cwd('/allData/5000/{}/{}'.format(product, year))
        url = '{}allData/5000/{}/{}/'.format(url, product, year)
    else:
        ftp.cwd('/allData/{}/{}/{}'.format(collection, product, year))
        url = '{}allData/{}/{}/{}/'.format(url.collection, product, year)

    # search for files
    url_list = []
    for i in range(day[0], day[1]+1):
        file_list = ftp.nlst('./{:03}'.format(i))
        pattern = re.compile('{}\.A{}{:03}\.h{:02}v{:02}\.{:03}.*\.h5'.format(
                                product, year, i, tile[0], tile[1], collection))
        url_list.extend(url + '{:03}/'.format(i) + x.split('/')[-1] for x in
                        file_list if re.search(pattern, x))

    # done
    if len(url_list) == 0:
        log.info('Found nothing.')
        return 1
    else:
        return url_list


def download(url, des, overwrite=False,ftp='NA'):
    """ Download and save a file from ftp

    Args:
      url (str): the link to the file
      des (str): destination to save the file
      overwrite (bool): overwrite or not
      ftp (FTP): an FTP object

    Returns:
      0: successful
      1: error due to des
      2: error due to url or ftp

    """
    do_not_quit = True

    # check if file already exists
    if (not overwrite) and os.path.isfile(des):
        log.error('{} already exists.'.format(des.split('/')[-1]))
        return 1

    # parse url
    url_split = url.split('://')[-1].split('/')
    n = len(url_split)

    # connect to ftp if not given ftp object
    if not isinstance(ftp,FTP):
        # check address
        if n < 2:
            log.error('Invalid address: {}'.format(url))
            return 2

        # connect to ftp
        ftp = get_ftp(url_split[0])
        do_not_quit = False
        if isinstance(ftp, int):
            return 2

    # download file
    try:
        ftp.retrbinary('RETR /{}'.format('/'.join(url_split[1:n])),
                        open(des, 'wb').write)
    except:
        log.error('{}...failed.'.format(url))
        return 2

    # complete download
    log.info('{}...completed.'.format(url_split[-1]))
    if not do_not_quit:
        ftp.quit()

    # done
    return 0


# main function
def download_data(url, des, sensor, collection, product, tile, year, day):
    """ Download a set of MODIS or VIIRS data from FTP

    Args:
      url (str): ftp address
      sensor (str): V for VIIRS, M for MODIS
      collection (int): 5 or 6 for MODIS, 1 for VIIRS
      product (str): which product (e.g. MOD09GA)
      tile (list, int): tile, [h, v]
      year (int): which year
      day (list, int): which day, 0 for all yea, [start, stop] for range

    Returns:
      0: successful
      1: connecting error
      2: cannot locate files
      3: cannot create output

    """
    # connect to ftp
    log.info('Connecting to FTP.')
    ftp = get_ftp(url)
    if isinstance(ftp, int):
        return 1
    log.info('Connection established.')

    # locate files
    log.info('Locating files.')
    file_list = locate_data(ftp, sensor, collection, product, tile, year, day)
    if isinstance(file_list, list):
        n = len(file_list)
        log.info('Found {} files.'.format(n))
    else:
        return 2

    # check output location
    if not os.path.exists(des):
        try:
            os.makedirs(des)
        except:
            log.error('Cannot create output folder {}'.format(des))
            return 3
    
    # download files
    if not des[-1] == '/':
        des = des + '/'
    log.info('Downloading files.')
    count = 0
    for f in file_list:
        if download(f,(des+f.split('/')[-1]),False,ftp) == 0:
            count = count + 1

    # done
    log.info('Download completed.')
    log.info('Successfully downloaded {}/{} files.'.format(count,n))
    return 0


# download data
if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
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
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # check if arguments and options are valid
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
    log.info('From {}'.format(_FTP))
    log.info('Saving in {}'.format(args.des))
    download_data(_FTP, args.des, args.sensor, args.collection, args.product,
                    args.tile, args.year, args.day)
