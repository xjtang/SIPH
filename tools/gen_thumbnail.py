""" Module for generating thumbnail for gtif files
"""
from __future__ import division
import os
import sys
import argparse
import numpy as np
from osgeo import gdal
from PIL import Image
from ..common import log, get_files, manage_batch


IMGMAX = 255
MASK_COLOR = (255, 0, 0)


def gen_tn(img, des, comp=[3,2,1], stretch=[0,5000], mask=0,
                overwrite=False, verbose=False, combo=False):
    """ Generage thumbnail for gtif image files

    Args:
      img (str): the link to the gtif image file
      des (str): destination to save the output preview image
      comp (list, int): band composite, [red, green, blue]
      stretch (list, int): stretch, [min, max]
      mask (int): mask band, 0 for no mask
      overwrite (bool): overwrite or not
      verbose (bool): verbose or not
      combo (bool): combine image and mask

    Returns:
      0: successful
      1: error due to des
      2: error due to generation of thumbnail
      3: error due to writing output

    """
    _error = 0

    # check if output already exists
    if (not overwrite) and os.path.isfile(des):
        log.error('{} already exists.'.format(des.split('/')[-1]))
        return 1

    # flow control
    while True:
        # read iamge
        if verbose:
            log.info('Reading input image...')
        try:
            img2 = gdal.Open(img, gdal.GA_ReadOnly)
            r = img2.GetRasterBand(comp[0]).ReadAsArray().astype(np.int16)
            g = img2.GetRasterBand(comp[1]).ReadAsArray().astype(np.int16)
            b = img2.GetRasterBand(comp[2]).ReadAsArray().astype(np.int16)
            if mask > 0:
                mask2 = img2.GetRasterBand(mask).ReadAsArray().astype(np.int16)
        except:
            _error = 2
            log.error('Failed to read input image {}'.format(img))
            break

        # generate preview
        if verbose:
            log.info('Generating thumbnail...')
        try:
            output = np.stack((r, g, b), axis = 2)
            output[output < stretch[0]] = stretch[0]
            output[output > stretch[1]] = stretch[1]
            output = ((output - stretch[0]) / (stretch[1] - stretch[0])
                        * IMGMAX).astype(np.uint8)
        except:
            _error = 2
            log.error('Failed to generate thumbnail.')
            break

        # apply mask
        if mask > 0:
            if verbose:
                log.info('Applying mask...')
            try:
                if combo:
                    output2 = np.array(output)
                    output2[mask2 > 0] = MASK_COLOR
                    output = np.concatenate((output,
                                                np.zeros((output.shape[1], 1,
                                                3), np.uint8) + 255, output2),
                                                axis=1).astype(np.uint8)
                    output2= None
                else:
                    output[mask2 > 0] = MASK_COLOR
            except:
                _error = 2
                log.error('Failed to apply mask band.')
                break

        # write output
        if verbose:
            log.info('Writing output...')
        try:
            img_out = Image.fromarray(output, 'RGB')
            img_out.save(des)
            img_out = None
        except:
            _error = 3
            log.error('Failed to write output to {}'.format(des))
            break

        # continue next
        break

    # closing files
    if verbose:
        log.info('Closing files...')
    img2 = None
    r = None
    g = None
    b = None
    mask2 = None
    output = None

    # done
    if _error == 0:
        if verbose:
            log.info('Process completed.')
    return _error


def batch_gen_tn(pattern, ori, des, overwrite=False, batch=[1,1], comp=[3,2,1],
                    stretch=[0,5000], mask=0, combo=False):
    """ Generage thumbnail for gtif image files

    Args:
      pattern (str): searching pattern, e.g. VNP*gtif
      ori (str): place to look for imputs
      des (str): place to save outputs
      overwrite (bool): overwrite or not
      batch (list, int): batch processing, [thisjob, totaljob]
      comp (list, int): band composite, [red, green, blue]
      stretch (list, int): stretch, [min, max]
      mask (int): mask band, 0 for no mask
      overwrite (bool): overwrite or not
      verbose (bool): verbose or not
      combo (bool): combine image and mask

    Returns:
      0: successful
      1: error due to des
      2: error when searching files
      3: found no file
      4: error during processing

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
    log.info('Locating files...'.format(ori))
    try:
        img_list = get_files(ori, pattern)
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
    log.info('Start generating thumbnails...')
    for img in img_list:
        log.info('Processing {}'.format(img[1]))
        if gen_tn('{}/{}'.format(img[0], img[1]), '{}/{}.jpg'.format(des,
                    img[1].split('.')[0]), comp, stretch, mask, overwrite,
                    False, combo) == 0:
            count += 1

    # done
    log.info('Process completed.')
    log.info('Successfully generated {}/{} thumnails.'.format(count, n))
    return 0


# generating thumbnails
if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--pattern', action='store', type=str,
                        dest='pattern', default='VNP*tif',
                        help='searching pattern')
    parser.add_argument('-b', '--batch', action='store', type=int, nargs=2,
                        dest='batch', default=[1,1],
                        help='batch process, [thisjob, totaljob]')
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite or not')
    parser.add_argument('-c', '--comp', action='store', type=int, nargs=3,
                        dest='comp', default=[3,2,1], help='band composite')
    parser.add_argument('-s', '--stretch', action='store', type=int, nargs=2,
                        dest='stretch', default=[0,5000], help='image stretch')
    parser.add_argument('-m', '--mask', action='store', type=int, dest='mask',
                        default=0, help='mask band, 0 for no mask')
    parser.add_argument('--combo', action='store_true',
                        help='combine mask image with original image')
    parser.add_argument('ori', default='./', help='origin')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # check arguments
    if not 1 <= args.batch[0] <= args.batch[1]:
        log.error('Invalid batch inputs: [{}, {}]'.format(args.batch[0],
                    args.batch[1]))
        sys.exit(1)
    if args.combo and args.mask == 0:
        log.error('For combined thumbnail you need to give a mask band.')
        sys.exit(1)

    # print logs
    log.info('Start generating thumbnails...')
    log.info('Running job {}/{}'.format(args.batch[0], args.batch[1]))
    log.info('Looking for {}'.format(args.pattern))
    log.info('In {}'.format(args.ori))
    log.info('Saving in {}'.format(args.des))
    log.info('Band composite:[{}, {}, {}]'.format(args.comp[0], args.comp[1],
                                                    args.comp[2]))
    log.info('Image stretch: [{}, {}]'.format(args.stretch[0], args.stretch[1]))
    if args.mask > 0:
        log.info('Mask band: {}'.format(args.mask))
    else:
        log.info('No mask band.')
    if args.combo:
        log.info('Combining masked image with original image.')

    # run function to download data
    batch_gen_tn(args.pattern, args.ori, args.des, args.overwrite, args.batch,
                    args.comp, args.stretch, args.mask, args.combo)
