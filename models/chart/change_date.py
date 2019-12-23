""" Module for generating change date maps from YATSM results

    Args:
        -t (period): study time period, start and end
        -R (recursive): recursive when seaching files
        --overwrite: overwrite or not
        ori: origin
        des: destination
        img: an example image to get the spatial reference

"""
import os
import argparse
import numpy as np

from osgeo import gdal

from ...common import log, get_files, show_progress, ordinal_to_doy
from ...common import constants as cons
from ...io import stackGeo, array2stack, chkExist, yatsm2records


def cdate(ori, des, img, period=[2001, 2016], overwrite=False,
                recursive=False):
    """ generate change date maps from YATSM results

    Args:
        ori (str): place to look for inputs
        des (str): output path and filename
        img (str): path to example image
        period (list, int): study time period in year, [start, end]
        overwrite (bool): overwrite or not
        recursive (bool): recursive when searching file, or not

    Returns:
        0: successful
        1: error due to des
        2: error when reading example image
        3: processed nothing

    """
    # check if output already exists if not create one
    if chkExist(des, True) > 0:
        return 1

    # get image spatial reference
    log.info('Reading spatial reference from: {}'.format(img))
    try:
        geo = stackGeo(img)
    except:
        log.error('Failed to read spatial reference from {}'.format(img))
        return 2

    # initialize output
    log.info('Initializing output...')
    r = np.zeros((geo['lines'], geo['samples'], period[1] - period[0] + 1),
                    np.int16) + cons.NODATA
    count = 0

    # generate results
    log.info('Start generating map...')
    for i in range(0, geo['lines']):
        try:
            yatsm = get_files(ori, 'yatsm_r{}.npz'.format(i), recursive)
            if len(yatsm) > 0:
                records = yatsm2records(os.path.join(yatsm[0][0], yatsm[0][1]))
                if len(records) > 0:
                    for record in records:
                        if record['break'] > 0:
                            px = record['px']
                            year = ordinal_to_doy(record['break']) // 1000
                            doy = ordinal_to_doy(record['break']) - (year*1000)
                            r[i, px, year - period[0]] = doy
                count += 1
            else:
                log.warning('Found no YATSM file for line {}'.format(i + 1))
                continue
        except:
            log.warning('Failed to process line {}.'.format(i + 1))
            continue
        progress = show_progress(i, geo['lines'], 5)
        if progress >= 0:
            log.info('{}% done.'.format(progress))
    if count == 0:
        log.error('Processed nothing.')
        return 3

    # write output
    log.info('Writing output to: {}'.format(des))
    for i in range(period[0], period[1] + 1):
        if array2stack(r[:, :, i - period[0]], geo,
                        os.path.join(des, '{}.tif'.format(i)),
                        'Change date for year {}'.format(i), cons.NODATA,
                        gdal.GDT_Int16, overwrite) > 0:
            log.error('Failed to write output for year {}.'.format(i))

    # done
    log.info('Process completed.')
    log.info('{}/{} lines successful.'.format(count, geo['lines']))
    return 0


if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--period', action='store', type=int, nargs=2,
                        dest='period', default=[2001,2016],
                        help='year, [start, end]')
    parser.add_argument('-R', '--recursive', action='store_true',
                        help='recursive or not')
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite or not')
    parser.add_argument('ori', default='./', help='origin')
    parser.add_argument('des', default='./', help='destination')
    parser.add_argument('img', default='./', help='example image')
    args = parser.parse_args()

    # print logs
    log.info('Start generating change date maps...')
    log.info('Files in {}'.format(args.ori))
    log.info('Saving in {}'.format(args.des))
    log.info('Copy spatial reference from {}'.format(args.img))
    log.info('Map from {} to {}.'.format(args.period[0], args.period[1]))
    if args.recursive:
        log.info('Recursive seaching.')
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to generatet change date maps from YATSM results
    cdate(args.ori, args.des, args.img, args.period, args.overwrite,
            args.recursive)
