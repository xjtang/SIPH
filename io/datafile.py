""" Module for IO of non-image files
"""
import os
import csv
import ast


def csv2list(_file, header=False, fixType=True):
    """ read a csv file based table to a list

    Args:
        file (str): path to input text file
        header (bool): first line header or not
        fixType (bool): convert data to correct type or not

    Returns:
        table (list): the table

    """
    # read file
    with open(_file, 'rb') as f:
        reader = csv.reader(f)
        if header:
            next(reader)
        table = list(reader)

    # fix data type
    if fixType:
        for i, row in enumerate(table):
            for j, value in enumerate(row):
                try:
                    table[i][j] = ast.literal_eval(value)
                except:
                    pass

    # done
    return table


def csv2dict(_file, fixType=True):
    """ read a csv file based table to a dictionary

    Args:
        file (str): path to input text file
        asDic (bool): convert data to correct type or not

    Returns:
        table (list): the table

    """
    # read file
    with open(_file, 'rb') as f:
        reader = csv.DictReader(f)
        table = list(reader)

    # fix data type
    if fixType:
        for i, row in enumerate(table):
            for key in row:
                try:
                    table[i][key] = ast.literal_eval(table[i][key])
                except:
                    pass

    # done
    return table
