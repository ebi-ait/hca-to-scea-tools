import logging
import os
import sys
import unittest
from collections import namedtuple
from subprocess import Popen, PIPE

import pandas as pd

HcaToSceaOutput = namedtuple('HcaToSceaOutput', ['output_dir', 'stdout', 'stderr'])


class CharacteristicTest(unittest.TestCase):

    def setUp(self):
        self.verificationErrors = {}
        self.output_base = 'output/'
        if not sys.warnoptions:
            import warnings
            warnings.simplefilter("ignore")

    def test_positive(self):
        arguments_df = pd.read_csv("test/golden/arguments.csv", comment='#')
        for i in range(0,arguments_df.shape[0]):
            spreadsheet = "test/golden/" + list(arguments_df['spreadsheet'])[i]
            with self.subTest(spreadsheet="test/golden/" + list(arguments_df['spreadsheet'])[i]):
                arguments = arguments_df.loc[arguments_df['spreadsheet'] == os.path.basename(spreadsheet)]
                tool_output = self.run_tool(spreadsheet, arguments)
                self.check_output(tool_output, spreadsheet)


    def test_negative(self):
        arguments_df = pd.read_csv("test/negative.examples.csv", comment='#')
        for i in range(0,arguments_df.shape[0]):
            spreadsheet = "test/golden/" + list(arguments_df['spreadsheet'])[i]
            with self.subTest(spreadsheet="test/golden/" + list(arguments_df['spreadsheet'])[i]):
                arguments = arguments_df.loc[arguments_df['spreadsheet'] == spreadsheet.split("test/golden/")[1]]
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

    def check_output(self, tool_otuput, spreadsheet):
        golden_output_dir = 'test/golden/expected/' + os.path.basename(spreadsheet).split(".xlsx")[0]
        for golden_file in os.listdir(golden_output_dir):
            golden_file_basename = os.path.basename(golden_file)
            output_file = os.path.join(tool_otuput.output_dir, golden_file_basename)
            golden_contents = self.get_file_content(os.path.join(golden_output_dir, golden_file_basename))
            output_contents = self.get_file_content(output_file)
            try:
                if isinstance(golden_contents, pd.DataFrame):
                    self.assert_dataframes_equal(golden_contents, output_contents, tag=golden_file_basename)
                else:
                    self.check_equal_lines(golden_contents, output_contents, f'diffs found comparing {golden_file_basename}')
            except Exception as e:
                raise AssertionError(f'problem with {golden_file}\nstdout:\n{tool_otuput.stdout}\nstderr\n{tool_otuput.stderr}\n') from e

    def run_tool(self, spreadsheet, arguments):
        output_name = os.path.basename(spreadsheet).split(".xlsx")[0]
        output_dir = self.output_base + output_name
        arguments = arguments.reset_index()
        p = Popen(["python3", 'hca2scea.py',
                   '-s', f'{spreadsheet}',
                   '-o', f'{output_dir}',
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
        return HcaToSceaOutput(output_dir, stdout, stderr)


if __name__ == '__main__':
    unittest.main()