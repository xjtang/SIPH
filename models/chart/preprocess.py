""" Module for preprocess MODIS data products (vi, lc, or nbar)

    Args:
        -p (pattern): searching pattern
        -d (product): vi, lc or nbar
        -b (batch): batch process, thisjob and totaljob
        -R (recursive): recursive when seaching files
        --overwrite: overwrite or not
        ori: origin
        des: destination

"""
import os
import sys
import argparse

from ...common import log, get_files, manage_batch
from ...io import (modisvi2stack, modislc2stack, nbar2stack, pheno2stack,
                    nbarcmg2stack, modisvicmg2stack, MOD09Q12stack,
                    MOD44B2stack)


def modis_product_preprocess(pattern, ori, des, product, overwrite=False,
                                recursive=False, batch=[1,1]):
    """ preprocess MODIS data product

    Args:
        pattern (str): searching pattern, e.g. MOD13Q1*hdf
        ori (str): place to look for inputs
        des (str): place to save outputs
        product (str): lc, vi, or nbar
        overwrite (bool): overwrite or not
        recursive (bool): recursive when searching file, or not
        batch (list, int): batch processing, [thisjob, totaljob]

    Returns:
        0: successful
        1: error due to des
        2: error when searching files
        3: found no file

    """
    # check if output exists, if not try to create one
    if not os.path.exists(des):
        log.warning('{} does not exist, trying to create one.'.format(des))
        try:
            os.makedirs(des)
        except:
            log.error('Cannot create output folder {}'.format(des))
            return 1

    # locate files
    log.info('Locating files...')
    try:
        img_list = get_files(ori, pattern, recursive)
        n = len(img_list)
    except:
        log.error('Failed to search for {}'.format(pattern))
        return 2
    else:
        if n == 0:
            log.error('Found no {}'.format(pattern))
            return 3
        else:
            log.info('Found {} files.'.format(n))

    # handle batch processing
    if batch[1] > 1:
        log.info('Handling batch process...')
        img_list = manage_batch(img_list, batch[0], batch[1])
        n = len(img_list)
        log.info('{} files to be processed by this job.'.format(n))

    # loop through all files
    count = 0
    log.info('Start processing files...')
    for img in img_list:
        log.info('Processing {}'.format(img[1]))
        if product == 'vi':
            if modisvi2stack(os.path.join(img[0], img[1]), des, overwrite) == 0:
                count += 1
        elif product == 'vicmg':
            if modisvicmg2stack(os.path.join(img[0], img[1]), des,
                                overwrite) == 0:
                count += 1
        elif product == 'lc':
            if modislc2stack(os.path.join(img[0], img[1]), des, False,
                                overwrite) == 0:
                count += 1
        elif product == 'nbar':
            if nbar2stack(os.path.join(img[0], img[1]), des, overwrite) == 0:
                count += 1
        elif product == 'pheno':
            if pheno2stack(os.path.join(img[0], img[1]), des, overwrite) == 0:
                count += 1
        elif product == 'nbarcmg':
            if nbarcmg2stack(os.path.join(img[0], img[1]), des, overwrite) == 0:
                count += 1
        elif product == '8day':
            if MOD09Q12stack(os.path.join(img[0], img[1]), des, overwrite) == 0:
                count += 1
        elif product == 'vcf':
            if MOD44B2stack(os.path.join(img[0], img[1]), des, overwrite) == 0:
                count += 1
        else:
            log.error('Unsupported product {}'.format(product))
            return 4

    # done
    log.info('Process completed.')
    log.info('Successfully processed {}/{} files.'.format(count, n))
    return 0


if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--pattern', action='store', type=str,
                        dest='pattern', default='MOD13Q1*hdf',
                        help='searching pattern')
    parser.add_argument('-d', '--product', action='store', type=str,
                        dest='product', default='vi',
                        help='which product, vi, lc, or nbar')
    parser.add_argument('-b', '--batch', action='store', type=int, nargs=2,
                        dest='batch', default=[1,1],
                        help='batch process, [thisjob, totaljob]')
    parser.add_argument('-R', '--recursive', action='store_true',
                        help='recursive or not')
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite or not')
    parser.add_argument('ori', default='./', help='origin')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # check arguments
    if not 1 <= args.batch[0] <= args.batch[1]:
        log.error('Invalid batch inputs: [{}, {}]'.format(args.batch[0],
                    args.batch[1]))
        sys.exit(1)

    # print logs
    log.info('Start preprocessing...')
    log.info('Running job {}/{}'.format(args.batch[0], args.batch[1]))
    log.info('Looking for {}'.format(args.pattern))
    log.info('In {}'.format(args.ori))
    log.info('Saving in {}'.format(args.des))
    log.info('Product is {}'.format(args.product))
    if args.recursive:
        log.info('Recursive seaching.')
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to preprocess data
    modis_product_preprocess(args.pattern, args.ori, args.des, args.product,
                                args.overwrite, args.recursive, args.batch)
