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
import json
import numpy as np

class DatFile():
    """
    """
    def __init__(self, dat_file_name=None, table_file='T_OBJ_ATTR.json', encoding='cp1250'):
        """ initialize """
        self.dat_file_name = dat_file_name

        self.dat_file = None
        self.tables_data = None
        try:
            self.dat_file = open(self.dat_file_name, 'r', encoding=encoding)
        except IOError:
            # handle IO rasied errors
            print("I/O operation error while trying to open "+self.dat_file_name)
        except UnicodeEncodeError:
            # Raised when a Unicode-related encoding error occurs
            print("There was an error encrypting "+self.dat_file_name+\
                " using "+encoding+" encoding")
        
        # Opening DAT1-M1 table's JSON file
        with open( table_file, 'r', encoding='cp1250') as f_tables:
            # returns JSON object as a dictionary
            self.tables_data = json.load(f_tables)
        
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

            return self.point_table[i][2]/100, self.point_table[i][1]/100

        return None
    
    def get_border_line(self, bid, reverse=False):
        """Get border line's point coordinates by border line id
        :param bid: border line id (type: int)
        :param reverse: reversing the direction of a line (type: bool)
        """
        selected_line = self.border_line_table[self.border_line_table[:,0] == bid]

        if selected_line.shape[0] == 0:
            return None

        selected_points = np.zeros((selected_line.shape[0]+1), dtype=int)
        selected_points[:-1] = selected_line[:,2]
        selected_points[-1] = selected_line[-1,3]

        selected_points_crd = [tuple(self.get_point(i)) for i in selected_points]

        if reverse:
            return selected_points_crd[::-1] #reverse
            
        return selected_points_crd

    def get_border(self, boid):
        """
        Retrieves the coordinates of a specified border by boid.
        
        Parameters:
        boid (int): The border identifier.
        
        Returns:
        selected_border_crd (list): A list of tuples representing the coordinates of the  border.
        Returns None if the boid is not found.
        """
   
        selected_border = self.border_table[self.border_table[:,0] == boid]


        if selected_border.shape[0] == 0:
            return None

        selected_border_crd_lists = [ self.get_border_line(selected_border[i,2], True) if selected_border[i,3] == -1
                                    else self.get_border_line(selected_border[i,2], False)
                                    for i in range(selected_border.shape[0]) ]

        selected_border_crd_list = sum(selected_border_crd_lists, []) #list of lists to a list of tuples

        # removing neighboring duplicated coordinates
        selected_border_crd = [selected_border_crd_list[0]]

        for i, point_crd in enumerate(selected_border_crd_list[1:]):
            if point_crd != selected_border_crd_list[i]:
                selected_border_crd.append(point_crd)

        return selected_border_crd

    def get_surface(self, sid):
        """
        Retrieves the coordinates of a specified surface by sid.

        Parameters:
        sid (int): The surface identifier.

        Returns:
        selected_surface_crd (list): A list of tuples representing the coordinates of the  border.
        Returns None if the boid is not found.
        """

        pre_selected = self.surface_table[self.surface_table[:,0] == sid]

        # exterior border to the first place
        selected_surface = pre_selected[(-pre_selected[:, 3]).argsort()]


        if selected_surface.shape[0] == 0:
            return None

        selected_surface_crd_lists = [self.get_border(selected_surface[i,2]) for i in range(selected_surface.shape[0])]

        return selected_surface_crd_lists
  
    def get_geometry_str(self, element, geom_type):
        """Create a postGIS EWKT string for geometry

        Parameters:
        element (list or tuple): coordinates of a point, line or polygon
        geom_type (str): Type of the element's geometry [point, line, surface]

        Returns:
        geometry (str): EWKT geometry string
        """
        if geom_type == 'surface':
            geometry = 'ST_geomfromEWKT(\'SRID=23700; POLYGON('
            for i in range(len(element)):
                geometry += '('
                geometry += ", ".join([str(crds[0])+' '+str(crds[1]) for crds in element[i]])
                geometry +=')'
                if len(element)-1 > i:
                    geometry += ','
            geometry += ')\')'


        elif geom_type == 'line':
            geometry = 'ST_geomfromEWKT(\'SRID=23700; LINE('
            geometry += ", ".join([str(crds[0])+' '+str(crds[1]) for crds in element])
            geometry += ')\')'


        elif geom_type == 'point':
            geometry = 'ST_geomfromEWKT(\'SRID=23700; POINT('
            geometry += f'{element[0]} {element[1]})\')'

        return geometry

    def create_tables(self, table_num='available'):
        """
        Retunrs a string with SQL create table commands.

        Filed names are defined in table_file according to DAT1-M1.
        Edit the table_file for additional checks and constraints.

        Default tabe_file name: T_OBJ_ATTR.json

        Parameters:
        table_num (str): tables to be created
                        - all: every table in table_file (A-B-C object tables)
                        - available: tables given in DAT file

        Returns:
        sql_string (str): fomrated string with SQL commands
        """
        selected_tables = []

        if table_num == 'available':
            for table_name in self.tables_data.keys():

                if table_name in self.table_info:
                    selected_tables.append(table_name)

        elif table_num == 'all':
            selected_tables = self.tables_data.keys()

        sql_string = ''
        constrain_string = '' # to add constraints at the end of the SQL string

        for obj_attrxx in selected_tables:

            fields = self.tables_data[obj_attrxx].get('fields')
            checks = self.tables_data[obj_attrxx].get('checks')
            constraints = self.tables_data[obj_attrxx].get('constraints')

            sql_string += f'CREATE TABLE {obj_attrxx}(\n'

            for field in fields.keys():
                sql_string += f'\t{field} {fields[field]},\n'

            sql_string += '\n'

            if checks:
                for check in checks.keys():
                    sql_string += f'\t{checks[check]}\n'

            sql_string += ');\n\n'

            if constraints:
                for constraint in constraints:
                    if constraint in selected_tables: #check if FK table created
                        constrain_string += f'{constraints[constraint]};\n'

        sql_string += constrain_string

        return sql_string



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

    print(D_F.create_tables()) # for test