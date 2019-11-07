
from __future__ import print_function

import os
import sys
import itertools
import copy
import pandas as pd

import muteria.common.mix as common_mix
import muteria.common.fs as common_fs

ERROR_HANDLER = common_mix.ErrorHandler

DEFAULT_KEY_COLUMN_NAME="MUTERIA_MATRIX_KEY_COL"
class RawExecutionMatrix(object):
    '''
        A 2D matrix representation of the execution of entities by test cases.
        Each entity is represented as a 'key' (The keys are unique) 
        on each row, and, the test cases represented as columns. 
        The behavior of each entity with regard to each test case 
        (affected or not) is represented as active or not. 
        The cell of the matrix with row key E and 
        column test case T represents whether T affects E.

        This class represent a configurable implementation of the Matrix.


        Parameters
        ----------
        filename : file system path string representing the filename where the 
                    underlying pandas dataframe of the matrix is stored
        key_column_name : The string representing the pandas dataframe column 
                        name that will be used to represent the entity ('key')
        non_key_col_list : list containing the list of strings representing
                        the test cases (pandas dataframe column that are not
                        used as key)
        active_cell_default_val : default value of the matrix cell among
                        those considered as active
        inactive_cell_vals : list containing the matrix cell values that are 
                        considered as inactive
        uncertain_cell_default_val : default value of the matrix cell among
                        those considered as uncertain
        is_active_cell_func : function that check whether a cell is active.
                        It takes the cell value as single parameter and returns
                        True if active and False otherwise
        is_inactive_cell_func : function that check whether a cell is inactive.
                        It takes the cell value as single parameter and returns
                        True if active and False otherwise
        is_uncertain_cell_func : function that check whether a cell is N/A.
                        It takes the cell value as simgle parameter and returns
                        True if uncertain (N/A) and False otherwise
        cell_dtype : data type that will be used in underlying pandas dataframe
                        to represent a cell.

        Note
        ---- 
        To ensure consistency in cell type and others, define an extension of 
        this class with fixed values except filename and non_key_col_list
        see for example ExecutionMatrix below.
    '''

    def __init__(self, filename=None, key_column_name=DEFAULT_KEY_COLUMN_NAME,
                    non_key_col_list=None, active_cell_default_val=[1], 
                    inactive_cell_vals=[0], uncertain_cell_default_val=[-1],
                    is_active_cell_func=lambda x: x > 0, 
                    is_inactive_cell_func=lambda x: x == 0, 
                    is_uncertain_cell_func=lambda x: x < 0,
                    cell_dtype=int):
        self.filename = filename
        self.key_column_name = key_column_name
        self.non_key_col_list = non_key_col_list
        self.active_cell_default_val = active_cell_default_val
        self.inactive_cell_vals = inactive_cell_vals
        self.uncertain_cell_default_val = uncertain_cell_default_val
        self.is_active_cell_func = is_active_cell_func
        self.is_inactive_cell_func = is_inactive_cell_func
        self.is_uncertain_cell_func = is_uncertain_cell_func

        # Verify 
        ERROR_HANDLER.assert_true(self.is_active_cell_func(\
                                self.active_cell_default_val[0]), "", __file__)
        ERROR_HANDLER.assert_true(self.is_inactive_cell_func(\
                                    self.inactive_cell_vals[0]), "", __file__) 
        ERROR_HANDLER.assert_true(self.is_uncertain_cell_func(\
                            self.uncertain_cell_default_val[0]), "", __file__)
        # Verify inactive
        for v in self.inactive_cell_vals:
            ERROR_HANDLER.assert_true(not self.is_active_cell_func(v), \
                                                                "", __file__)
        for v in self.inactive_cell_vals:
            ERROR_HANDLER.assert_true(not self.is_uncertain_cell_func(v), \
                                                                "", __file__)

        if self.filename is None or not os.path.isfile(self.filename):
            ERROR_HANDLER.assert_true(self.non_key_col_list is not None, \
                                    "Must specify 'non_key_col_list' when " + \
                                    "filename inexistant. filename is " +
                                    str(self.filename), __file__)
            ordered_cols = [self.key_column_name] + self.non_key_col_list
            self.dataframe = \
                    pd.DataFrame({c:[] for c in ordered_cols})[ordered_cols]
            self.dataframe = self.dataframe.astype(cell_dtype)\
                                           .astype({self.key_column_name: str})
        else:
            self.dataframe = common_fs.loadCSV(self.filename)
            #ERROR_HANDLER.assert_true(len(self.dataframe.columns) >= 2, \
            #        "expect at least 2 columns in dataframe: key, values...",\
            #                                                        __file__)
            ERROR_HANDLER.assert_true(self.key_column_name == \
                                    list(self.dataframe)[0], "key_column"\
                            " name missing or not first column in dataframe",\
                                                                    __file__)
            if self.non_key_col_list is None:
                self.non_key_col_list = list(self.dataframe)[1:]
            else:
                ERROR_HANDLER.assert_true(self.non_key_col_list == \
                                list(self.dataframe)[1:], "non key mismatch",\
                                                                    __file__)

        self.keys_set = set(self.get_keys())

    def get_a_deepcopy(self, new_filename=None, serialize=True):
        """ get a copy of the current matrix. The new filename will be 
            used fo storage.
        :param new_filename: filename to store the copy
        :param serialize: (bool) decide whether to serialize the copy to 
                            file upon creation
        :return: a deep copy of this matrix

        Example:
        >>> nc = ['a', 'b', 'c']
        >>> mat = ExecutionMatrix(non_key_col_list=nc)
        >>> mat.add_row_by_key('k', [1, 2, 3])
        >>> c_mat = mat.get_a_deepcopy()
        >>> mat.dataframe.equals(c_mat.dataframe)
        True
        >>> mat.add_row_by_key('r', [1, 2, 3])
        >>> mat.dataframe.equals(c_mat.dataframe)
        False
        """
        ret_matrix = copy.deepcopy(self)
        ret_matrix.filename = new_filename
        if serialize:
            ret_matrix.serialize()
        return ret_matrix

    def getActiveCellDefaultVal(self):
        """ Get a value that represent an active cell value
        """
        return self.active_cell_default_val[0]
        
    def getInactiveCellVal(self):
        """ Get a value that represent an inactive cell value
        """
        return self.inactive_cell_vals[0]

    def getUncertainCellDefaultVal(self):
        """ Get a value that represent an uncertain cell value
        """
        return self.uncertain_cell_default_val[0]

    def serialize(self):
        """ Serialize the matrix to its corresponding file if not None
        """
        if self.filename is not None:
            common_fs.dumpCSV(self.dataframe, self.filename)
    #~ def serialize()

    def get_store_filename(self):
        """ Get the name of the storing file
        """
        return self.filename
    #~ def get_store_filename()

    #def raw_add_row(self):

    #def raw_delete_row(self):

    def add_row_by_key(self, key, values, serialize=True):
        """ add a row to the matrix
        :param key: The key to add
        :param values: (list or dict) The values for the given key.
                        Ordered following non key columns ordering if list
                        if dict, it is mapping from column name to value
        :param serialize: (bool) decide whether to serialize the matrix to 
                        file after adding
        :return: nothing

        Example:
        >>> nc = ['a', 'b', 'c']
        >>> mat = ExecutionMatrix(non_key_col_list=nc)
        >>> mat.add_row_by_key('k', [1, 2, 3])
        >>> mat._get_key_values_dict(['k']) == {'k': {'a':1,'b':2,'c':3}}
        True
        >>> mat.add_row_by_key('r', {'a':3, 'c':2, 'b':3})
        >>> mat._get_key_values_dict(['r']) == {'r': {'a':3,'b':3,'c':2}}
        True
        >>> len(mat.get_keys())
        2
        """
        ERROR_HANDLER.assert_true(key not in self.keys_set, \
                            "adding an existing key: '"+str(key)+\
                            "', to matrix: " + str(self.filename), __file__)
        self.keys_set.add(key)
        if type(values) in (list, tuple):
            self.dataframe.loc[len(self.dataframe)] = [key] + values
        elif type(values) == dict:
            ERROR_HANDLER.assert_true(self.key_column_name not in values, \
                                        "key column name in values", __file__)
            tmpdict = {self.key_column_name: key}
            tmpdict.update(values)
            self.dataframe = self.dataframe.append(tmpdict, ignore_index=True)
        else:
            ERROR_HANDLER.error_exit("Invald input: 'values'", __file__)

        if serialize:
            self.serialize()

    def delete_rows_by_key(self, key_list, serialize=True):
        """ delete the rows for the given keys
        :param key_list: collection of key whose rows to delete
        :param serialize: (bool) decide whether to serialize the matrix
                         to file after deletion
        :return: nothing

        Example:
        >>> nc = ['a', 'b', 'c']
        >>> mat = ExecutionMatrix(non_key_col_list=nc)
        >>> mat.add_row_by_key('k', [1, 2, 3])
        >>> mat.add_row_by_key('r', [3, 2, 3])
        >>> mat.add_row_by_key('w', [1, 0, 3])
        >>> mat.delete_rows_by_key(['k','w'])
        >>> mat_keys = mat.get_keys()
        >>> len(mat_keys)
        1
        >>> mat_keys[0] == 'r'
        True
        """
        self.dataframe = \
            self.dataframe.loc[~self.dataframe[self.key_column_name]\
                                                        .isin(set(key_list))]
        self.dataframe = self.dataframe.reset_index(drop=True)

        if serialize:
            self.serialize()

    def to_pandas_df(self):
        """ return the matrix as a pandas dataframe 
            (just return a copy of the underlying pandas dataframe)
        :return: a deep copy of the underlying pandas dataframe 
                (modifying the dataframe do ot affect the matrix)

        Example:
        >>> nc = ['a', 'b', 'c']
        >>> mat = ExecutionMatrix(non_key_col_list=nc)
        >>> mat.add_row_by_key('k', [1, 2, 3])
        >>> df2 = mat.to_pandas_df()
        >>> mat.add_row_by_key('r', [3, 2, 3])
        >>> len(df2)
        1
        >>> len(mat.get_keys())
        2
        """
        return self.dataframe.copy(deep=True)

    def get_key_colname(self):
        """ get the name of the column representing the keys
        """
        return self.key_column_name

    def get_nonkey_colname_list(self):
        """ get list of non key columns
        Example:
        >>> nc = ['a', 'b', 'c']
        >>> mat = ExecutionMatrix(non_key_col_list=nc)
        >>> mat.get_nonkey_colname_list() == nc
        True
        >>> mat.add_row_by_key('k', [1, 2, 3])
        >>> mat.get_nonkey_colname_list() == nc
        True
        """
        return self.non_key_col_list

    def get_keys(self):
        """ get a pandas serie of the keys (example mutant ids)
        Example:
        >>> nc = ['a', 'b', 'c']
        >>> mat = ExecutionMatrix(non_key_col_list=nc)
        >>> type(mat.get_keys()) == pd.core.series.Series
        True
        >>> len(mat.get_keys())
        0
        >>> mat.add_row_by_key('k', [1, 2, 3])
        >>> list(mat.get_keys())
        ['k']
        """
        return self.dataframe[self.key_column_name]

    def is_empty(self):
        """ Check that the matrix have no row (all columns have no row)
        Example:
        >>> nc = ['a', 'b', 'c']
        >>> mat = ExecutionMatrix(non_key_col_list=nc)
        >>> mat.is_empty()
        True
        >>> mat.add_row_by_key('k', [1, 2, 3])
        >>> mat.is_empty()
        False
        """
        return len(self.get_keys()) == 0

    def extract_by_rowkey(self, row_key_list, out_filename=None):
        """ get the sub-matrix with the rows keys corresponding to the
            values in the passed list.
            Note that the order of keys in row_key_list is not guaranted
        :param row_key_list: collection of row keys to extract. 
                            Must not be empty and every key must exist
        :param out_filename: Optional filename to use as storage for the 
                            extracted matrix. Default is None (no storage)
        :return: matrix which is sub matrix of this

        Example:
        >>> nc = ['a', 'b', 'c']
        >>> mat = ExecutionMatrix(non_key_col_list=nc)
        >>> mat.add_row_by_key('k', [1, 2, 3])
        >>> mat.add_row_by_key('r', [3, 2, 3])
        >>> mat.add_row_by_key('w', [1, 0, 3])
        >>> mat2 = mat.extract_by_rowkey(['r', 'k'])
        >>> list(mat2.get_keys()) == ['k', 'r']
        True
        >>> mat2.get_nonkey_colname_list() == nc
        True
        """
        ERROR_HANDLER.assert_true(len(row_key_list) > 0, \
                                    "key list should not be empty", __file__)
        ERROR_HANDLER.assert_true(len(set(row_key_list) - self.keys_set) == 0,\
                                    "invalid row key passed to extract row", \
                                                                    __file__)

        ret = self.get_a_deepcopy(new_filename=out_filename, serialize=True)
        ret.dataframe = ret.dataframe.loc[ret.dataframe[ret.key_column_name]\
                                                        .isin(row_key_list)]
        ret.keys_set = set(ret.get_keys())
        return ret

    def extract_by_column(self, non_key_col_list, out_filename=None):
        """ get the sub-matrix with the columns corresponding to the
            values in the passed list.
            Note that the order is maintained if a list is passed
        :param non_key_col_list: collection of columns to extract. 
                            Must not be empty and every column must exist
        :param out_filename: Optional filename to use as storage for the 
                            extracted matrix. Default is None (no storage)
        :return: matrix which is sub matrix of this

        Example:
        >>> nc = ['a', 'b', 'c']
        >>> mat = ExecutionMatrix(non_key_col_list=nc)
        >>> mat.add_row_by_key('k', [1, 2, 3])
        >>> mat.add_row_by_key('r', [3, 2, 3])
        >>> mat.add_row_by_key('w', [1, 0, 3])
        >>> mat2 = mat.extract_by_column(['a', 'c'])
        >>> list(mat2.get_keys()) == ['k', 'r', 'w']
        True
        >>> mat2.get_nonkey_colname_list() == ['a', 'c']
        True
        """
        ERROR_HANDLER.assert_true(len(non_key_col_list) > 0, \
                                    "col list should not be empty", __file__)
        ERROR_HANDLER.assert_true(len(set(non_key_col_list) - \
                                        set(self.non_key_col_list)) == 0, \
                                    "invalid column passed to extract col", \
                                                                    __file__)
        non_key_col_list = list(non_key_col_list)
        ret = self.get_a_deepcopy(new_filename=out_filename, serialize=True)
        ret.dataframe = ret.dataframe[[ret.key_column_name]+non_key_col_list]
        ret.non_key_col_list = non_key_col_list
        return ret

    def query_active_columns_of_rows(self, row_key_list=None):
        ''' return a dict in the form row2cols
        :param row_key_list: list of rows to query for
        :return: a dict representing a mapping between the passed rows
                and the list of columns active for those rows

        Example:
        >>> nc = ['a', 'b', 'c']
        >>> mat = ExecutionMatrix(non_key_col_list=nc)
        >>> act = mat.getActiveCellDefaultVal()
        >>> inact = mat.getInactiveCellVal()
        >>> uncert = mat.getUncertainCellDefaultVal()
        >>> mat.add_row_by_key('k', [inact, uncert, act])
        >>> mat.query_active_columns_of_rows() == {'k': ['c']}
        True
        '''
        if row_key_list is None:
            row_key_list = self.get_keys()

        result = {}
        if len(row_key_list) > 0:
            small_df = self.extract_by_rowkey(row_key_list).dataframe
            for _, row in small_df.iterrows():
                result[row[self.key_column_name]] = \
                                        [x for x in self.non_key_col_list \
                                        if self.is_active_cell_func(row[x])]

        return result
    #~ def query_active_columns_of_rows()

    def query_active_rows_of_columns(self, non_key_col_list=None):
        ''' return a dict in the form col2rows
        :param non_key_col_list: list of columns to query for
        :return: a dict representing a mapping between the passed columns
                and the list of rows active for those columns

        Example:
        >>> nc = ['a', 'b', 'c']
        >>> mat = ExecutionMatrix(non_key_col_list=nc)
        >>> act = mat.getActiveCellDefaultVal()
        >>> inact = mat.getInactiveCellVal()
        >>> uncert = mat.getUncertainCellDefaultVal()
        >>> mat.add_row_by_key('k', [inact, uncert, act])
        >>> mat.query_active_rows_of_columns() == {'a':[], 'b':[], 'c':['k']}
        True
        '''
        if non_key_col_list is None:
            non_key_col_list = self.non_key_col_list

        result = {}
        if len(non_key_col_list) > 0:
            small_df = self.extract_by_column(non_key_col_list).dataframe
            for col in non_key_col_list:
                result[col] = list(small_df.loc[\
                                small_df[col].apply(self.is_active_cell_func)]\
                                                        [self.key_column_name])

        return result
    #~ def query_active_rows_of_columns()

    def query_inactive_columns_of_rows(self, row_key_list=None):
        ''' return a dict in the form row2cols
        :param row_key_list: list of rows to query for
        :return: a dict representing a mapping between the passed rows
                and the list of columns inactive for those rows

        Example:
        >>> nc = ['a', 'b', 'c']
        >>> mat = ExecutionMatrix(non_key_col_list=nc)
        >>> act = mat.getActiveCellDefaultVal()
        >>> inact = mat.getInactiveCellVal()
        >>> uncert = mat.getUncertainCellDefaultVal()
        >>> mat.add_row_by_key('k', [inact, uncert, act])
        >>> mat.query_inactive_columns_of_rows() == {'k': ['a']}
        True
        '''
        if row_key_list is None:
            row_key_list = self.get_keys()

        result = {}
        if len(row_key_list) > 0:
            small_df = self.extract_by_rowkey(row_key_list).dataframe
            for _, row in small_df.iterrows():
                result[row[self.key_column_name]] = \
                                        [x for x in self.non_key_col_list \
                                        if self.is_inactive_cell_func(row[x])]

        return result
    #~ def query_inactive_columns_of_rows()

    def query_inactive_rows_of_columns(self, non_key_col_list=None):
        ''' return a dict in the form col2rows
        :param non_key_col_list: list of columns to query for
        :return: a dict representing a mapping between the passed columns
                and the list of rows inactive for those columns

        Example:
        >>> nc = ['a', 'b', 'c']
        >>> mat = ExecutionMatrix(non_key_col_list=nc)
        >>> act = mat.getActiveCellDefaultVal()
        >>> inact = mat.getInactiveCellVal()
        >>> uncert = mat.getUncertainCellDefaultVal()
        >>> mat.add_row_by_key('k', [inact, uncert, act])
        >>> mat.query_inactive_rows_of_columns() == {'a':['k'], 'b':[], 'c':[]}
        True
        '''
        if non_key_col_list is None:
            non_key_col_list = self.non_key_col_list

        result = {}
        if len(non_key_col_list) > 0:
            small_df = self.extract_by_column(non_key_col_list).dataframe
            for col in non_key_col_list:
                result[col] = list(small_df.loc[\
                            small_df[col].apply(self.is_inactive_cell_func)]\
                                                        [self.key_column_name])

        return result
    #~ def query_inactive_rows_of_columns()

    def query_uncertain_columns_of_rows(self, row_key_list=None):
        ''' return a dict in the form row2cols
        :param row_key_list: list of rows to query for
        :return: a dict representing a mapping between the passed rows
                and the list of columns uncertain for those rows

        Example:
        >>> nc = ['a', 'b', 'c']
        >>> mat = ExecutionMatrix(non_key_col_list=nc)
        >>> act = mat.getActiveCellDefaultVal()
        >>> inact = mat.getInactiveCellVal()
        >>> uncert = mat.getUncertainCellDefaultVal()
        >>> mat.add_row_by_key('k', [inact, uncert, act])
        >>> mat.query_uncertain_columns_of_rows() == {'k': ['b']}
        True
        '''
        if row_key_list is None:
            row_key_list = self.get_keys()

        result = {}
        if len(row_key_list) > 0:
            small_df = self.extract_by_rowkey(row_key_list).dataframe
            for _, row in small_df.iterrows():
                result[row[self.key_column_name]] = \
                                        [x for x in self.non_key_col_list \
                                        if self.is_uncertain_cell_func(row[x])]

        return result
    #~ def query_uncertain_columns_of_rows()

    def query_uncertain_rows_of_columns(self, non_key_col_list=None):
        ''' return a dict in the form col2rows
        :param non_key_col_list: list of columns to query for
        :return: a dict representing a mapping between the passed columns
                and the list of rows inactive for those columns

        Example:
        >>> nc = ['a', 'b', 'c']
        >>> mat = ExecutionMatrix(non_key_col_list=nc)
        >>> act = mat.getActiveCellDefaultVal()
        >>> inact = mat.getInactiveCellVal()
        >>> uncert = mat.getUncertainCellDefaultVal()
        >>> mat.add_row_by_key('k', [inact, uncert, act])
        >>> mat.query_uncertain_rows_of_columns() == {'a':[],'b':['k'],'c':[]}
        True
        '''
        if non_key_col_list is None:
            non_key_col_list = self.non_key_col_list

        result = {}
        if len(non_key_col_list) > 0:
            small_df = self.extract_by_column(non_key_col_list).dataframe
            for col in non_key_col_list:
                result[col] = list(small_df.loc[\
                            small_df[col].apply(self.is_uncertain_cell_func)]\
                                                        [self.key_column_name])

        return result
    #~ def query_uncertain_rows_of_columns()

    def _get_key_values_dict(self, keys=None):
        """ compute a dict object with key each element of keys and value
            the corresponding dict representation of the row(without the key)
        :param keys: list of keys of interest to get values. 
                        If None, all keys are considered
        :return: dict representing a mapping between the row keys and their 
                    row values. 
                    each row value is a dict of column to cell value

        Example:
        >>> nc = ['a', 'b', 'c']
        >>> mat = ExecutionMatrix(non_key_col_list=nc)
        >>> mat.add_row_by_key('k', [1, 2, 3])
        >>> mat._get_key_values_dict(['k']) == {'k': {'a':1,'b':2,'c':3}}
        True
        """
        if keys is None:
            keys = self.get_keys()
        if len(keys) == 0:
            k_v_dict = {}
        else:
            tmp_df = self.extract_by_rowkey(keys).dataframe
            tmp_df.set_index(self.get_key_colname(), inplace=True)
            k_v_dict = tmp_df.to_dict('index')
        return k_v_dict

    def update_cells(self, key, values):
        """ Update the values for the key with the values 
        :param key: key whose values to update
        :param values: dict representing the new cell values by column name
        :return: nothing

        Example:
        >>> nc = ['a', 'b', 'c']
        >>> mat = ExecutionMatrix(non_key_col_list=nc)
        >>> mat.add_row_by_key('k', [1, 2, 3])
        >>> mat.add_row_by_key('r', [1, 2, 3])
        >>> mat.update_cells('k', {'a':0, 'c':4})
        >>> mat._get_key_values_dict(['k']) == {'k': {'a':0, 'b':2, 'c':4}}
        True
        """
        # locate key index
        key_pos = self.dataframe\
                        .index[self.dataframe[self.get_key_colname()] == key]\
                        .tolist()
        ERROR_HANDLER.assert_true(len(key_pos) == 1)
        key_pos = key_pos[0]
        for col, cval in list(values.items()):
            self.dataframe.at[key_pos, col] = cval

    def update_with_other_matrix(self, other_matrix, \
                                override_existing=False, allow_missing=False, \
                                serialize=False):
        """ Update this matrix using the other matrix
        :param other_matrix: The matrix to use to update this matrix
        :param override_existing: (bool) decide whether existing cell's 
                        value (row, column) of this matrix should be 
                        overrided by the update.
                        Note that if this is disabled, no cell (row, col)
                        of this matrix must exist in other_matrix, or this
                        will fail.
        :param allow_missing: (bool) decide whether missing cell are allowed
                        when merging (cells that only belong to one matrix
                        while thre are other cells on same row or same 
                        column that belong to the two matrices).
                        Note that if this is disable. there should not be
                        any such cell during merging or this will fail.
        :param serialize: (bool) decides whether to serialize the updated
                        matrix (this matrix), after update, into its file.
        :return: nothing

        Example:
        >>> nc = ['a', 'b', 'c']
        >>> mat = ExecutionMatrix(non_key_col_list=nc)
        >>> mat.add_row_by_key('k', [1, 2, 3])
        >>> mat.add_row_by_key('r', [4, 0, 1])
        >>> nc_o = ['b', 'e']
        >>> mat_other = ExecutionMatrix(non_key_col_list=nc_o)
        >>> mat_other.add_row_by_key('h', [200, 100])
        >>> mat_other.add_row_by_key('r', [10, 11])
        >>> mat.update_with_other_matrix(mat_other, override_existing=True, \
                                                            allow_missing=True)
        >>> list(mat.get_keys())
        ['k', 'r', 'h']
        >>> list(mat.get_nonkey_colname_list())
        ['a', 'b', 'c', 'e']
        >>> k_v_d = mat._get_key_values_dict()
        >>> uncert = mat.getUncertainCellDefaultVal()
        >>> k_v_d['k'] == {'a': 1, 'b': 2, 'c': 3, 'e': uncert}
        True
        >>> k_v_d['r'] == {'a': 4, 'b': 10, 'c': 1, 'e': 11}
        True
        >>> k_v_d['h'] == {'a': uncert, 'b': 200, 'c': uncert, 'e': 100}
        True
        """
        #other_matrix_df = other_matrix.to_pandas_df()
        # Check values overlap
        row_existing = set(self.get_keys()) & set(other_matrix.get_keys())
        col_existing = set(self.get_nonkey_colname_list()) & \
                            set(other_matrix.get_nonkey_colname_list())
        if len(row_existing) > 0 and len(col_existing) > 0:
            ERROR_HANDLER.assert_true(override_existing, \
                            "Override_existing not set but there is overlap", \
                                                                    __file__)            

        # Check missing
        if len(row_existing) < len(other_matrix.get_keys()):
            #- Some rows will be added
            if len(col_existing) != len(self.get_nonkey_colname_list()) or \
                            len(col_existing) != \
                                len(other_matrix.get_nonkey_colname_list()):
                ERROR_HANDLER.assert_true(allow_missing, \
                                "allow_missing disable but there are missing",\
                                                                    __file__)

        # Actual update
        ## 1. Create columns that are not in others
        col_to_add = set(other_matrix.get_nonkey_colname_list()) - \
                                            set(self.get_nonkey_colname_list())
        for col in col_to_add:
            self.non_key_col_list.append(col)
            self.dataframe[col] = [self.getUncertainCellDefaultVal()] * \
                                                        len(self.get_keys())
        
        ## 2. Update or insert rows
        extra_cols = set(self.get_nonkey_colname_list()) - \
                                    set(other_matrix.get_nonkey_colname_list())
        missing_extracol_vals = {e_c: self.getUncertainCellDefaultVal() \
                                                        for e_c in extra_cols}
        ### Insert
        new_rows = set(other_matrix.get_keys()) - set(self.get_keys())
        k_v_dict = other_matrix._get_key_values_dict(new_rows)
        for key, values in list(k_v_dict.items()):
            values.update(missing_extracol_vals)
            self.add_row_by_key(key, values, serialize=False)
        ### Update
        k_v_dict = other_matrix._get_key_values_dict(row_existing)
        for key, values in list(k_v_dict.items()):
            for col in values:
                self.update_cells(key, values)

        if serialize:
            self.serialize()
    #~ def update_with_other_matrix()
#~ class RawExecutionMatrix

class ExecutionMatrix(RawExecutionMatrix):
    '''
        This class is the default extension of the class RawExecutionMatrix. 
    '''
    def __init__(self, filename=None, non_key_col_list=None):
        RawExecutionMatrix.__init__(self, filename=filename, \
                                            non_key_col_list=non_key_col_list)
    #~ def __init__()
#~ class ExecutionMatrix


class OutputLogData(object):
    #OBJECTIVE_ID = "OBJECTIVE_ID"
    #TEST_ID = "TEST_ID"
    OUTLOG_LEN = "OUTLOG_LEN"       # int
    OUTLOG_HASH = "OUTLOG_HASH"     # str
    RETURN_CODE = "RETURN_CODE"     # int
    TIMEDOUT = "TIMEDOUT"           # bool
    #ordered_cols = [OBJECTIVE_ID, TEST_ID, OUTLOG_LEN, OUTLOG_HASH, \
    #                                                            RETURN_CODE]
    Dat_Keys = {OUTLOG_LEN, OUTLOG_HASH, RETURN_CODE, TIMEDOUT}
    
    UNCERTAIN_TEST_OUTLOGDATA = {
                OUTLOG_LEN: common_mix.GlobalConstants.COMMAND_UNCERTAIN,
                OUTLOG_HASH: common_mix.GlobalConstants.COMMAND_UNCERTAIN,
                RETURN_CODE: common_mix.GlobalConstants.COMMAND_UNCERTAIN,
                TIMEDOUT: common_mix.GlobalConstants.COMMAND_UNCERTAIN,
    }

    @classmethod
    def outlogdata_equiv(cls, outlogdata1, outlogdata2):
        if outlogdata1 == cls.UNCERTAIN_TEST_OUTLOGDATA or \
                                outlogdata2 == cls.UNCERTAIN_TEST_OUTLOGDATA:
            return None
        if outlogdata1 != outlogdata2 and not(\
                    outlogdata1[cls.TIMEDOUT] and outlogdata2[cls.TIMEDOUT]):
            return False
        return True
    #~ def outlogdata_diff()

    def __init__(self, filename=None):
        self.filename = filename
        if self.filename is None or not os.path.isfile(self.filename):
            self.data = {}
        else:
            self.data = common_fs.loadJSON(self.filename)
    #~ def __init__()

    def is_empty(self):
        return len(self.data) == 0
    #~ def is_empty()

    def get_zip_objective_and_data(self):
        return self.data.items()
    #~ def get_zip_objective_and_data()

    def add_data (self, data_dict, check_all=True, override_existing=False, 
                                                            serialize=False):
        if check_all:
            ERROR_HANDLER.assert_true(\
                            type(data_dict) == dict and len(data_dict) > 0, \
                                        "expecting a non empty dict", __file__)
            for o, o_obj in data_dict.items():
                if len(o_obj) == 0: 
                    continue
                ERROR_HANDLER.assert_true(\
                            type(o_obj) == dict, \
                            "expecting dict for value data: objective is "+o, \
                                                                    __file__)
                for t, t_obj in o_obj.items():
                    ERROR_HANDLER.assert_true(set(t_obj) == self.Dat_Keys , \
                                "Invalid data for o "+o+' and t '+t, __file__)

        intersect_objective = set(self.data) & set(data_dict)
        onlynew_objective = set(data_dict) - intersect_objective
        if not override_existing:
            for objective in intersect_objective:
                ERROR_HANDLER.assert_true(len(set(self.data[objective]) & \
                                            set(data_dict[objective])) == 0, \
                            "Override_existing not set but there is overlap", \
                                                                    __file__)            
        for objective in intersect_objective:
            self.data[objective].update(data_dict[objective])
        for objective in onlynew_objective:
            self.data[objective] = copy.deepcopy(data_dict[objective])
        if serialize:
            self.serialize()
    #~ def add_data ()

    def update_with_other(self, other_execoutput, \
                                    override_existing=False, serialize=False):
        self.add_data(other_execoutput.data, check_all=False, \
                                        override_existing=override_existing, \
                                        serialize=serialize)
    #~ def update_with_other_matrix()

    def serialize(self):
        """ Serialize the matrix to its corresponding file if not None
        """
        if self.filename is not None:
            common_fs.dumpJSON(self.data, self.filename, pretty=True)
    #~ def serialize()

    def get_store_filename(self):
        """ Get the name of the storing file
        """
        return self.filename
    #~ def get_store_filename()
#~ class OutputLogData
