import logging
import os
import sys
import unittest
import pandas as pd
import numpy as np
from pandas.testing import assert_frame_equal


class CharacteristicTest(unittest.TestCase):

    def setUp(self):
        self.verificationErrors = {}
        self.output_base = 'output/'
        if not sys.warnoptions:
            import warnings
            warnings.simplefilter("ignore")

    def test_hca2scea_characteristic(self):
        # run tool
        arguments_df = pd.read_csv("test/golden/arguments.csv", comment='#')
        for i in range(0,arguments_df.shape[0]):
            spreadsheet = "test/golden/" + list(arguments_df['spreadsheet'])[i]
            with self.subTest(spreadsheet="test/golden/" + list(arguments_df['spreadsheet'])[i]):
                arguments = arguments_df.loc[arguments_df['spreadsheet'] == os.path.basename(spreadsheet)]
                output_dir = self.run_tool(spreadsheet, arguments)
                self.check_output(output_dir, spreadsheet)

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
                           sep='^([^\t]+)\t',
                           engine='python',
                           usecols=[0, 1, 2],
                           names=['idx', 'name', 'value'])

    def load_sdrf_file(self, file):
        return pd.read_csv(file, sep='\t')

    def assert_dataframes_equal(self, golden_contents, output_contents, tag=None):
        difference_locations = golden_contents != output_contents
        changed_from = golden_contents[difference_locations].dropna(how='all')
        changed_to = output_contents[difference_locations].dropna(how='all')
        diff:pd.DataFrame = changed_from.join(changed_to,
                                              lsuffix='_expected', rsuffix='_actual',
                                              sort=False)

        diff = diff.melt()
        if len(diff) != 0:
            diff_file = f'{self.output_base}/diff.html'
            if tag:
                diff_file = f'{self.output_base}/diff-{tag}.html'
            diff.to_html(diff_file)
        assert len(diff) == 0, f'diffs found comparing {tag}\n{diff.to_string()}'

    def check_equal_lines(self, golden_contents, output_contents, msg=None):
        self.assertMultiLineEqual(golden_contents,output_contents, msg)

    def check_output(self, output_dir, spreadsheet):
        golden_output_dir = 'test/golden/expected/' + os.path.basename(spreadsheet).split(".xlsx")[0]
        for golden_file in os.listdir(golden_output_dir):
            golden_file_basename = os.path.basename(golden_file)
            output_file = os.path.join(output_dir, golden_file_basename)
            golden_contents = self.get_file_content(os.path.join(golden_output_dir, golden_file_basename))
            output_contents = self.get_file_content(output_file)
            try:
                if isinstance(golden_contents, pd.DataFrame):
                    self.assert_dataframes_equal(golden_contents, output_contents, tag=golden_file_basename)
                else:
                    self.check_equal_lines(golden_contents, output_contents, f'diffs found comparing {golden_file_basename}')
            except Exception as e:
                raise AssertionError(f'problem with {golden_file}') from e
    def run_tool(self, spreadsheet, arguments):
        output_name = os.path.basename(spreadsheet).split(".xlsx")[0]
        output_dir = self.output_base + output_name
        arguments = arguments.reset_index()
        os.system(
            f'python3 hca2scea.py -s {spreadsheet} -o {output_dir} -id {arguments["HCA project uuid"][0]} -ac {arguments["E-HCAD accession"][0]} -c {arguments["curator initials"][0]} -et {arguments["experiment type"][0]} -f {arguments["factor values"][0]} -pd {arguments["public release date"][0]} -hd {arguments["hca last update date"][0]} -study {arguments["study accession"][0]}')
        return output_dir

if __name__ == '__main__':
    unittest.main()
