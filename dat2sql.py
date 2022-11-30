#! /usr/bin/env python3

"""
    Hungarian standard DAT file to SQL script converter

    Used data structures:

    table_info
    dictionary where keys are the table names (e.g. T_PONT or T_OBJ_ATTRBD) and
    holds a list of three elements (start_position_of_table, end_position_of_table, number_of_rows)

    point_table
    an ordered numpy 2D array by the point ids, a row holds data for a point: id, east, north
"""

# TODO should we use elevations in point_table? 2D or 3D?
# TODO load T_VONAL, T_HATARVONAL, T_HATAR and T_FELULET
# TODO method to get a point, line or surface geometry (collected from geometry tables)
#      use search sorted to search in sorted numpy arrays

import sys
import re
import numpy as np

class DatFile():
    """
    """
    def __init__(self, dat_file_name=None, encoding='cp1250'):
        """ initialize """
        self.dat_file_name = dat_file_name
        try:
            self.dat_file = open(self.dat_file_name, 'r', encoding=encoding)
        except:
            self.dat_file = None
        # geometry tables
        self.point_table = None
        self.line_table = None
        self.border_line_table = None
        self.border_table = None
        self.surface_table = None
        self.table_info = None

    def load_table_info(self):
        """ get table positions and number of lines from dat file """
        self.dat_file.seek(0)   # rewind file
        table_start = re.compile('T_')
        table_info = {}
        table_name = None
        act_line = self.dat_file.readline()
        num_lines = 0
        while act_line:
            if table_start.match(act_line):     # new table start
                if table_name is not None:      # store end and size to previous table
                    table_info[table_name].append(self.dat_file.tell() - len(act_line))
                    table_info[table_name].append(num_lines-1)
                table_name = act_line.strip('*\n\r \t')
                table_info[table_name] = [self.dat_file.tell()]     # store start position in file
                num_lines = 0   # restart row counter
            act_line = self.dat_file.readline()
            num_lines += 1
        if len(table_info[table_name]) == 1:    # add end and size to last table
            table_info[table_name].append(self.dat_file.tell())
            table_info[table_name].append(num_lines-1)
        self.table_info = table_info

    def load_points(self, force = False):
        """ load all points into memory (numpy array)
            :param force: force load even if points were loaded yet
        """
        if self.point_table is not None and not force:
            return
        # TODO use structure array with int and float data types
        point_table = np.zeros((self.table_info['T_PONT'][2], 3), dtype=float)
        self.dat_file.seek(self.table_info['T_PONT'][0])   # move to start of data
        for i in range(self.table_info['T_PONT'][2]):
            act_line = self.dat_file.readline().strip('*\n\r \t')
            act_buf = act_line.split('*')
            for j in range(3):
                point_table[i, j] = float(act_buf[j])   # TODO use list comprehension instead of for loop
        self.point_table = point_table[point_table[:, 0].argsort()] # sort by id

if __name__ == "__main__":
    if len(sys.argv) > 1:
        D_F = DatFile(sys.argv[1])
        D_F.load_table_info()
        D_F.load_points()
        print(D_F.point_table.shape)