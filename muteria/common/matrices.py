
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
        assert self.is_active_cell_func(self.active_cell_default_val)
        assert self.is_inactive_cell_func(self.inactive_cell_vals)
        assert self.is_uncertain_cell_func(self.uncertain_cell_default_val)
        # Verify inactive
        for v in self.inactive_cell_vals:
            assert not self.is_active_cell_func(v)
        for v in self.inactive_cell_vals:
            assert not self.is_uncertain_cell_func(v)

        if self.filename is None or not os.path.isfile(self.filename):
            assert self.non_key_col_list is not None, \
                                    "Must specify 'non_key_col_list' when " + \
                                        "filename inexistant"
            ordered_cols = [self.key_column_name] + self.non_key_col_list
            self.dataframe = \
                    pd.DataFrame({c:[] for c in ordered_cols})[ordered_cols]
            self.dataframe = self.dataframe.astype(cell_dtype)\
                                           .astype({self.key_column_name: str})
        else:
            self.dataframe = common_fs.loadCSV(self.filename)
            assert len(self.dataframe.columns) >= 2, \
                    "expect at least 2 columns in dataframe: key, values..."
            assert self.key_column_name == list(self.dataframe)[0], \
                    "key_column name missing or not first column in dataframe"
            if self.non_key_col_list is None:
                self.non_key_col_list = list(self.dataframe)[1:]
            else:
                assert self.non_key_col_list == list(self.dataframe)[1:], \
                                                            "non key mismatch"

        self.keys_set = set(self.get_keys())

    def get_a_deepcopy(self, new_filename=None):
        ret_matrix = copy.deepcopy(self)
        if new_filename is not None:
            ret_matrix.filename = new_filename
        return ret_matrix

    def getActiveCellDefaultVal(self):
        return self.active_cell_default_val[0]
        
    def getInactiveCellVal(self):
        return self.inactive_cell_vals[0]

    def getUncertainCellDefaultVal(self):
        return self.uncertain_cell_default_val[0]

    def serialize(self):
        if self.filename is not None:
            common_fs.dumpCSV(self.dataframe, self.filename)

    #def raw_add_row(self):

    #def raw_delete_row(self):

    def add_row_by_key(self, key, values, serialize=True):
        assert key not in self.keys_set, "adding an existing key: "+str(key)
        self.keys_set.add(key)
        if type(values) in (list, tuple):
            self.dataframe.loc[len(self.dataframe)] = [key] + values
        elif type(values) == dict:
            assert self.key_column_name not in values, \
                                                    "key column name in values"
            tmpdict = {self.key_column_name: key}
            tmpdict.update(values)
            self.dataframe.append(tmpdict, ignore_index=True)
        else:
            assert False, "Invald input: 'values'" 

        if serialize:
            self.serialize()

    def delete_rows_by_key(self, key_list, serialize=True):
        self.dataframe = \
            self.dataframe.ix[~self.dataframe[self.key_column_name]\
                                                        .isin(set(key_list))]

        if serialize:
            self.serialize()

    def get_pandas_df(self):
        return self.dataframe

    def get_key_colname(self):
        return self.key_column_name

    def get_nonkey_colname_list(self):
        return self.non_key_col_list

    def get_keys(self):
        return self.dataframe[self.key_column_name]

    def is_empty(self):
        return len(self.get_keys()) == 0

    def extract_by_rowkey(self, row_key_list):
        return self.dataframe.loc[self.dataframe[self.key_column_name]\
                                                        .isin(row_key_list)]

    def extract_by_column(self, non_key_col_list):
        return self.dataframe[[self.key_column_name]+non_key_col_list]

    def query_active_columns_of_rows(self, row_key_list=None):
        '''
            return a dict in the form row2cols
        '''
        if row_key_list is None:
            row_key_list = self.get_keys()

        result = {}
        small_df = self.extract_by_rowkey(row_key_list)
        for _, row in small_df.iterrows():
            result[row[self.key_column_name]] = \
                                        [x for x in self.non_key_col_list \
                                        if self.is_active_cell_func(row[x])]

        return result

    def query_active_rows_of_columns(self, non_key_col_list=None):
        '''
            return a dict in the form col2rows
        '''
        if non_key_col_list is None:
            non_key_col_list = self.non_key_col_list

        result = {}
        small_df = self.extract_by_column(non_key_col_list)
        for col in small_df:
            result[col] = list( \
                small_df.loc[~small_df[col].isin(self.inactive_cell_vals)]\
                                                        [self.key_column_name])

        return result

    def _get_key_values_dict(self, keys):
        tmp_df = self.extract_by_rowkey(keys)
        tmp_df.set_index(self.get_key_colname())
        k_v_dict = tmp_df.to_dict('index')
        return k_v_dict

    def _update_cells(self, key, values):
        # locate key index
        key_pos = self.dataframe\
                        .index[self.dataframe[self.get_key_colname()] == key]\
                        .tolist()
        ERROR_HANDLER.assert_true(len(key_pos) == 1)
        key_pos = key_pos[0]
        for col, cval in list(values.items()):
            self.dataframe.at[key_pos, col] = cval

    def update_with_other_matrix(self, other_matrix, 
                                override_existing=False, allow_missing=False, \
                                serialize=False):
        #other_matrix_df = other_matrix.get_pandas_df()
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
                                                            len(self.get_keys)
        
        ## 2. Update or insert rows
        extra_cols = set(self.get_keys()) - set(other_matrix.get_keys())
        missing_extracol_vals = {e_c: self.getUncertainCellDefaultVal() \
                                                        for e_c in extra_cols}
        ### Insert
        new_rows = set(other_matrix.get_keys()) - set(self.get_keys())
        k_v_dict = other_matrix._get_key_value_dict(new_rows)
        for key, values in list(k_v_dict.items()):
            values.update(missing_extracol_vals)
            self.add_row_by_key(key, values, serialize=False)
        ### Update
        k_v_dict = other_matrix._get_key_value_dict(row_existing)
        for key, values in list(k_v_dict.items()):
            for col in values:
                self._update_cells(key, values)

        if serialize:
            self.serialize()

class ExecutionMatrix(RawExecutionMatrix):
    '''
        This class is the default extension of the class RawExecutionMatrix. 
    '''
    def __init__(self, filename=None, non_key_col_list=None):
        RawExecutionMatrix.__init__(self, filename=filename, \
                                            non_key_col_list=non_key_col_list)

