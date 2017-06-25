""" Module for reading non-image files
"""
import os
import csv
import ast


def csv2list(_file, header=False, fixType=True):
    """ read a csv file based table to a list

    Args:
        file (str): path to input text file
        header (bool): first line header or not
        asDic (bool): save as dic, must have header

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
