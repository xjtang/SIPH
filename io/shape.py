""" Module for IO of vector files
"""
import os

from shapely import geometry as geo, affinity as aff
from fiona import collection
from fiona.crs import from_epsg

from . import csv2dict
from ..common import log


def csv2shape(ori, des, shp, epsg=3857, overwrite=False, verbose=False):
    """ read csv file of information about shapes and export as a shapefile

    Args:
        ori (str): path to input csv file
        des (str): path to output shapefile
        shp (str): what shape is the input file
        epsg (int): coordinate system in EPSG
        overwrite (bool): overwrite or not
        verbose (bool): verbose or not

    Returns:
        0: successful
        1: error due to des
        2: error in reading input
        3: error in generating output

    """
    # check if output already exists
    if (not overwrite) and os.path.isfile(des):
        log.error('{} already exists.'.format(des.split('/')[-1]))
        return 1

    # read csv file
    if verbose:
        log.info('Reading input csv file...')
    try:
        shp_list = csv2dict(ori)
    except:
        log.error('Failed to rad input csv file: {}'.format(ori.split('/')[-1]))
        return 2

    # generate shapa and write output
    if verbose:
        log.info('Generating output...')
    if shp == 'point':
        shp2 = 'Point'
    else:
        shp2 = 'Polygon'
    try:
        _schema = {'geometry': shp2, 'properties': {'PID': 'str'}}
        with collection(des, "w", crs = from_epsg(epsg),
                        driver = "ESRI Shapefile", schema = _schema) as f:
            for i, row in enumerate(shp_list):
                if shp == 'ellipse':
                    _shape = draw_ellipse(row['x'], row['y'], row['a'],
                                            row['b'], 90 - row['r'])
                elif shp == 'point':
                    _shape = geo.Point(row['x'], row['y'])
                elif shp == 'circle':
                    _point = geo.Point(row['x'], row['y'])
                    _shape = _point.buffer(row['r'])
                else:
                    log.error('Unknown shape: {}'.format(shp))
                    return 3
                f.write({'properties': {'PID': row['id']},
                            'geometry': geo.mapping(_shape)})
    except:
        log.error('Error occured while generating output.')
        return 3

    # done
    if verbose:
        log.info('Process completed.')
    return 0


def draw_ellipse(x, y, a, b, r):
    """ create a ellise shape based on input information

    Args:
        x (float): x coordinates of center
        y (float): y coordinates of center
        a (float): major axis
        b (float): minor axis
        r (float): rotation in degree

    Returns:
        _ellipse2 (shape): shape object of the ellipse
        -1: error

    """
    # generate ellipse
    _point = geo.Point(x, y)
    _circle = _point.buffer(1)
    _ellipse = aff.scale(_circle, a, b)
    _ellipse2 = aff.rotate(_ellipse, r)

    # clean up
    _point = None
    _circle = None
    _ellipse = None

    return _ellipse2
