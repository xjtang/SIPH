""" Module for downloading VIIRS or MODIS product from ftp
"""
import os
import argparse
import logging
from datetime import datetime as dt

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.info('asd')

FTP = 'ftp://ladsweb.nascom.nasa.gov/allData/'

def locate_data(ftp, sensor, platform, collection, product, tile, year, day):
    """ Locate the data file on ftp based on download criteria

    Args:
      sensor (str): V for VIIRS, M for MODIS
      platform (str): T for Terra, A for Aqua, or B for both (use B for VIIRS)
      collection (int): 5 or 6 for MODIS, 1 for VIIRS
      product (str): which product (e.g. MOD09GA)
      h (int): horizontal tile
      v (int): vertical tile
      year (int): which year
      day (int): which day

    Returns:
        str: link to the file

    """

    return 0


def download(url, des, overwrite):
    """ Download and save a file from Internet

    Args:
      url (str): the link to the file
      des (str): destination to save the file
      overwrite (bool): overwrite or not

    Returns:
      0: successful

    """

    if (not overwrite) and os.path.isfile(des):
        log.info()

    return 0


# main function
def download_data(ftp, des, sensor, platform, collection, product, tile, year):
    """ Download a set of MODIS or VIIRS data from FTP

    Args:
      sensor (str): V for VIIRS, M for MODIS
      platform (str): T for Terra, A for Aqua, or B for both (use B for VIIRS)
      collection (int): 5 or 6 for MODIS, 1 for VIIRS
      product (str): which product (e.g. MOD09GA)
      h (int): horizontal tile
      v (int): vertical tile
      year (int): which year

    Returns:
        0: successful

    """

    print(ftp)
    print(des)
    print(sensor)
    print(platform)
    print(collection)
    print(product)
    print(tile)
    print(year)

    return 0


# download data
if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--sensor', action='store', type=str,
                        dest='sensor', default='V',
                        help='V for VIIRS, M for MODIS')
    parser.add_argument('-p', '--platform', action='store', type=str,
                        dest='platform', default='B',
                        help='T:Terra, A:Aqua, or B:Both (use B for VIIRS)')
    parser.add_argument('-c', '--collection', action='store', type=int,
                        dest='collection', default=1,
                        help='5 or 6 for MODIS, 1 for VIIRS')
    parser.add_argument('-d', '--product', action='store', type=str,
                        dest='product', default='VNP09GA',
                        help='which product (e.g. MOD09GA)')
    parser.add_argument('-t', '--tile', action='store', type=int, nargs=2,
                        dest='tile', default=[12,9], help='tile, h and v')
    parser.add_argument('-y','--year', action='store', type=int, dest='year',
                        default=dt.now().year, help='which year')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # check if arguments and options are valid
    if args.sensor == 'V':
        if args.platform != 'B':
            parser.error('Invalid platform, use B for VIIRS.')
        if args.collection != 1:
            parser.error('Invalid collection, use 1 for VIIRS.')
        if args.product not in ['VNP09GA']:
            parser.error('Invalid product.')
    elif args.sensor == 'M':
        if args.platform not in ['T', 'A']:
            parser.error('Invalid platform, use T for Terra, A for Aqua.')
        if args.platform not in [5, 6]:
            parser.error('Invalid collection, use 5 or 6 for MODIS.')
        if args.product not in ['MOD09GA']:
            parser.error('Invalid product.')
    else:
        parser.error('Invalid sensor, use M for MODIS V for VIIRS.')
    if not 0 <= args.tile[0] <= 35:
        parser.error('Invalid tile h, must be between 0 and 35.')
    if not 0 <= args.tile[1] <= 35:
        parser.error('Invalid tile v, must be between 0 and 35.')

    # run function to download data
    log.warning('nimalaobi')
    download_data(FTP, args.des, args.sensor, args.platform, args.collection,
                    args.product, args.tile, args.year)
