import logging
import os
import shutil
import sys
import unittest
from numpy import nan
from collections import namedtuple
from subprocess import Popen, PIPE

import pandas as pd

HcaToSceaOutput = namedtuple('HcaToSceaOutput', ['output_dir', 'stdout', 'stderr'])

BASE_DIR = os.path.dirname(__file__)
TEST_DIR = os.path.join(BASE_DIR, "test")

class CharacteristicTest(unittest.TestCase):

    def setUp(self):
        self.output_dir = None
        self.verificationErrors = {}
        self.output_base = os.path.join(BASE_DIR, 'output/')
        if not sys.warnoptions:
            import warnings
            warnings.simplefilter("ignore")

    def test_positive(self):
        arguments_df = pd.read_csv(os.path.join(TEST_DIR, "golden/arguments.csv"), comment='#')
        for i in range(0,arguments_df.shape[0]):
            spreadsheet = os.path.join(TEST_DIR, "golden/", list(arguments_df['spreadsheet'])[i])
            with self.subTest(spreadsheet=spreadsheet):
                arguments = arguments_df.loc[arguments_df['spreadsheet'] == spreadsheet.split("golden/")[1]]
                tool_output = self.run_tool(spreadsheet, arguments)
                self.check_output(tool_output, spreadsheet)


    def test_negative(self):
        arguments_df = pd.read_csv(os.path.join(TEST_DIR, "negative.examples.csv"), comment='#')
        for i in range(0,arguments_df.shape[0]):
            spreadsheet = os.path.join(TEST_DIR, "golden/" , list(arguments_df['spreadsheet'])[i])
            with self.subTest(spreadsheet=spreadsheet):
                arguments = arguments_df.loc[arguments_df['spreadsheet'] == spreadsheet.split("golden/")[1]]
                tool_output = self.run_tool(spreadsheet, arguments)
                arguments = arguments.reset_index()
                self.assertIn(b'AssertionError', tool_output.stderr)
                self.assertIn(arguments["expected error"][0].encode('ascii'),
                              tool_output.stderr,
                              msg='expected assertion error message not found in tool output')


    def get_file_content(self, file):
        if file.split(".")[-2] == 'sdrf':
            file_contents = self.load_sdrf_file(file)
        elif file.split(".")[-2] == 'idf':
            file_contents = self.load_idf_file(file)
            logging.info(file_contents.head())
        elif file.split(".")[-1] == 'csv':
            file_contents = self.load_big_table_file(file)
        else:
            raise ValueError(f'unsupported test file format: {file}')
        return file_contents

    def load_big_table_file(self, file):
        return pd.read_csv(file, sep=';')

    def load_idf_file(self, file):
        return pd.read_csv(file,
                           sep='^([^\t]*)\t?',
                           engine='python',
                           usecols=[0, 1, 2],
                           names=['idx', 'name', 'value'])

    def load_sdrf_file(self, file):
        return pd.read_csv(file, sep='\t')

    def get_mage_type(self, df):
        if set(df.columns) == set(['idx', 'name', 'value']):
            return 'idf'
        if 'Source Name' in df.columns:
            return 'sdrf'
        raise ValueError(f'Cannot convey if file is IDF or SDRF using cols: {df.columns}')

    def get_sdrfs_even(self, df1, df2, extra_cols):
        for extra_col in extra_cols:
            if extra_col in df1.columns:
                df2[extra_col] = nan
            else:
                df1[extra_col] = nan
        df1 = df1.reindex(df2.columns, axis=1)
        return df1, df2
    
    def assert_sdrf_shape_equal(self, golden_contents, output_contents, tag=None):
        extra_cols = set(golden_contents.columns).symmetric_difference(output_contents.columns)
        golden_extra_cols = set(golden_contents.columns) - set(output_contents.columns)
        output_extra_cols = set(output_contents.columns) - set(golden_contents.columns)
        assert extra_cols == set(), f'number of fields mismatch {tag}\nexpected not found:{golden_extra_cols}\nunexpected and found:{output_extra_cols}'

    def assert_sdrf_contents_equal(self, golden_contents, output_contents, tag=None):
        extra_cols = set(golden_contents.columns).symmetric_difference(output_contents.columns)
        golden_contents, output_contents = self.get_sdrfs_even(golden_contents, output_contents, extra_cols)

        golden_contents = golden_contents.sort_values(by=['Source Name']).reset_index(drop=True)
        output_contents = output_contents.sort_values(by=['Source Name']).reset_index(drop=True)
        diff = golden_contents.compare(output_contents, result_names=('expected', 'actual'))

        diff = diff.melt(value_name='diff_value')
        if len(diff) != 0:
            diff_file = f'{self.output_dir}/diff{tag if tag else ""}.html'
            diff.to_html(diff_file)
        assert len(diff) == 0, f'output content differences found comparing {tag}\n{diff.to_string()}'

    def get_idf_dict(self, df):
        return {
            row["name"]: str(row["value"]).split("\t") if pd.notna(row["value"]) else []
            for _, row in df.iterrows()
            }
    
    def get_idf_even(self, dict1, dict2):
        extra_cols = set(dict2.keys()).symmetric_difference(set(dict1.keys()))
        if not extra_cols:
            return dict1, dict2
        full_cols = set(dict1.keys()).union(set(dict2.keys()))
        dict1 = {key: dict1.get(key, []) for key in full_cols}
        dict2 = {key: dict2.get(key, []) for key in full_cols}
        return dict1, dict2

    def assert_idf_shape_equal(self, golden_contents, output_contents, tag=None):
        extra_cols = set(golden_contents).symmetric_difference(set(output_contents))
        golden_extra_cols = set(golden_contents.keys()) - set(output_contents.keys())
        output_extra_cols = set(output_contents.keys()) - set(golden_contents.keys())
        assert extra_cols == set(), f'shape mismatch {tag}\nexpected:{golden_extra_cols}\nfound:{output_extra_cols}'

    def assert_idf_contents_equal(self, golden_contents, output_contents, tag=None):
        golden_even, output_even = self.get_idf_even(golden_contents, output_contents)
        for key in golden_even.keys():
            assert key in output_even, f'key not found {tag}\n{key}'
            assert golden_even[key] == output_even[key], f'value mismatch {tag}\n{key}\nexpected:{golden_even[key]}\nfound:{output_even[key]}'

    def check_output(self, tool_otuput, spreadsheet):
        golden_output_dir = os.path.join(TEST_DIR, 'golden/expected/', os.path.basename(spreadsheet).split(".xlsx")[0])
        for golden_file in os.listdir(golden_output_dir):
            golden_file_basename = os.path.basename(golden_file)
            output_file = os.path.join(tool_otuput.output_dir, golden_file_basename)
            golden_contents = self.get_file_content(os.path.join(golden_output_dir, golden_file_basename))
            output_contents = self.get_file_content(output_file)
            mage_type = self.get_mage_type(golden_contents)
            if mage_type == "sdrf":
                self.assert_sdrf_shape_equal(golden_contents, output_contents, tag=golden_file_basename)
                self.assert_sdrf_contents_equal(golden_contents, output_contents, tag=golden_file_basename)
            elif mage_type == "idf":
                golden_df = self.get_idf_dict(golden_contents)
                output_df = self.get_idf_dict(output_contents)
                self.assert_idf_shape_equal(golden_df, output_df, tag=golden_file_basename)
                self.assert_idf_contents_equal(golden_df, output_df, tag=golden_file_basename)

    def run_tool(self, spreadsheet, arguments):
        output_name = os.path.basename(spreadsheet).split(".xlsx")[0]
        self.output_dir = os.path.join(self.output_base, output_name)

        # Clear test folder
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
        os.makedirs(self.output_dir)

        arguments = arguments.reset_index()
        p = Popen(["python3", os.path.join(BASE_DIR, 'hca2scea.py'),
                   '-s', f'{spreadsheet}',
                   '-o', f'{self.output_dir}',
                   '-id', f'{arguments["HCA project uuid"][0]}',
                   '-ac', f'{arguments["E-HCAD accession"][0]}',
                   '-c', f'{arguments["curator initials"][0]}',
                   '-et', f'{arguments["experiment type"][0]}',
                   '-f', f'{arguments["factor values"][0]}',
                   '-pd', f'{arguments["public release date"][0]}',
                   '-hd', f'{arguments["hca last update date"][0]}',
                   '-study', f'{arguments["study accession"][0]}'],
                  stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        return HcaToSceaOutput(self.output_dir, stdout, stderr)


if __name__ == '__main__':
    unittest.main()