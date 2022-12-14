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

        self.dat_file = None
        try:
            self.dat_file = open(self.dat_file_name, 'r', encoding=encoding)
        except IOError:
            # handle IO rasied errors
            print("I/O operation error while trying to open "+self.dat_file_name)
        except UnicodeEncodeError:
            # Raised when a Unicode-related encoding error occurs
            print("There was an error encrypting "+self.dat_file_name+\
                " using "+encoding+" encoding")

        # geometry tables
        self.point_table = None
        self.line_table = None
        self.border_line_table = None
        self.border_table = None
        self.surface_table = None
        self.table_info = None

    def load_table_info(self):
        """ get table positions and number of lines from dat file """
        self.dat_file.seek(0)   # rewind file - tell = byte pozi/ seek
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

        point_table = np.zeros((self.table_info['T_PONT'][2], 3), dtype=int)
        self.dat_file.seek(self.table_info['T_PONT'][0])   # move to start of data

        for i in range(self.table_info['T_PONT'][2]):
            act_line = self.dat_file.readline().strip('*\n\r \t')
            act_buf = act_line.split('*')
            point_table[i] = [ int(act_buf[j]) if j == 0 else int(float(act_buf[j])*100) for j in range(3) ]

        self.point_table = point_table[point_table[:, 0].argsort()] # sort by id

    def load_lines(self, force = False):
        '''load all edges into memory (numpy array)
        :param force: force load even if lines have been loaded already
        '''
        if self.line_table is not None and not force:
            return

        try:
            self.table_info["T_VONAL"]
        except KeyError:
            print("No T_VONAL table in "+self.dat_file_name)
            return

        line_table = np.zeros((self.table_info['T_VONAL'][2], 4), dtype=int)
        self.dat_file.seek(self.table_info['T_VONAL'][0])   # move to start of data

        for i in range(self.table_info['T_VONAL'][2]):
            act_line = self.dat_file.readline().strip('*\n\r \t')
            act_buf = act_line.split('*')
            line_table[i] = [int(act_buf[j]) for j in range(4)]

        self.line_table = line_table[np.lexsort((line_table[:,1], line_table[:,0]))] # sort by id

    def load_border_lines(self, force = False):
        '''load all border lines into memory (numpy array)
        :param force: force load even if lines were loaded yet            
        '''
        if self.border_line_table is not None and not force:
            return

        border_line_table = np.zeros((self.table_info['T_HATARVONAL'][2], 4), dtype=int)
        self.dat_file.seek(self.table_info['T_HATARVONAL'][0])   # move to start of data

        for i in range(self.table_info['T_HATARVONAL'][2]):
            act_line = self.dat_file.readline().strip('*\n\r \t')
            act_buf = act_line.split('*')
            border_line_table[i] = [int(act_buf[j]) for j in range(4)]

        self.border_line_table = border_line_table[np.lexsort((border_line_table[:, 1],border_line_table[:, 0]))] # sort by id and sub_id


    def load_borders(self, force = False):
        '''load all borders into memory (numpy array)
           '+' rotation direction is replaced with '1'
           '-' rotation direction is replaced with '-1'
        :param force: force load even if lines were loaded yet            
        '''
        if self.border_table is not None and not force:
            return

        border_table = np.zeros((self.table_info['T_HATAR'][2], 4), dtype=int)
        self.dat_file.seek(self.table_info['T_HATAR'][0])   # move to start of data

        for i in range(self.table_info['T_HATAR'][2]):
            act_line = self.dat_file.readline().strip('*\n\r \t')
            act_line = act_line.replace('+', '1')      #replace '+' character to 1  
            act_line = act_line.replace('-', '-1')     #replace '-' character to -1
            act_buf = act_line.split('*')
            border_table[i] = [int(act_buf[j]) for j in range(4)]

        self.border_table = border_table[np.lexsort((border_table[:, 1],border_table[:, 0]))] # sort by id and sub_id

    def load_surfaces(self, force = False):
        '''load all surfacess into memory (numpy array)
           '+' rotation direction is replaced with '1'
           '-' rotation direction is replaced with '-1'
        :param force: force load even if lines were loaded yet            
        '''
        if self.surface_table is not None and not force:
            return

        surface_table = np.zeros((self.table_info['T_FELULET'][2], 4), dtype=int)
        self.dat_file.seek(self.table_info['T_FELULET'][0])   # move to start of data

        for i in range(self.table_info['T_FELULET'][2]):
            act_line = self.dat_file.readline().strip('*\n\r \t')
            act_line = act_line.replace('+', '1')      #replace '+' character to 1  
            act_line = act_line.replace('-', '-1')     #replace '-' character to -1
            act_buf = act_line.split('*')
            surface_table[i] = [int(act_buf[j]) for j in range(4)]

        self.surface_table = surface_table[np.lexsort((surface_table[:, 1],surface_table[:, 0]))] # sort by id and sub_id

    def get_point(self, pid):
        """Get point coordinates by point id
        :param pid: point id in point_table
        """
        i = np.searchsorted(self.point_table[:,0], pid )

        if 0 <= i < self.point_table.shape[0] and self.point_table[i,0] == pid:

            return self.point_table[i][1]/100, self.point_table[i][2]/100

        return None
    
    def get_border_line(self, bid):
        """Get border line's point coordinates by border line id
        :param bid: border line id (type: int)
        """
        selected_line = self.border_line_table[self.border_line_table[:,0] == bid]

        if selected_line.shape[0] == 0:
            return None

        selected_points = np.zeros((selected_line.shape[0]+1), dtype=int)
        selected_points[:-1] = selected_line[:,2]
        selected_points[-1] = selected_line[-1,3]

        i = np.searchsorted(self.point_table[:,0], selected_points )

        if 0 <= i.all() < self.point_table.shape[0] and self.point_table[i,0].all() == selected_points.all():

            selected_points_crd = list(zip(self.point_table[i,1]/100, self.point_table[i,2]/100))

            return selected_points_crd
        
        return None





if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} dat_file")
        sys.exit(1)

    D_F = DatFile(sys.argv[1])
    if D_F.dat_file is None:
        print(f"Cannot open dat file {sys.argv[1]}")
        sys.exit(2)
    D_F.load_table_info()
    D_F.load_points()
    print('point ids:')
    print(D_F.point_table.shape)
    print(D_F.point_table[0:10,:])

    D_F.load_lines()
    # print(D_F.line_table[0:10,:]) # for test
    print(D_F.line_table) # for test
    # print(D_F.line_table.shape)

    D_F.load_border_lines()
    print(D_F.border_line_table[0:5,:])  # for test      
    print(D_F.border_line_table.shape)        

    D_F.load_borders()
    print(D_F.border_table[2350:2360,:])  # for test +1 and -1 replacement
    print(D_F.border_table.shape)  

    D_F.load_surfaces()
    print(D_F.surface_table[110:116,:])  # for test +1 and -1 replacement     
    print(D_F.surface_table.shape)

    print(D_F.get_border_line(2)) # for test
