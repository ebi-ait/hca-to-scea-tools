import os
import sys
import unittest
import pandas as pd
from pandas._testing import assert_frame_equal

class CharacteristicTest(unittest.TestCase):

    def setUp(self):
        self.verificationErrors = {}
        if not sys.warnoptions:
            import warnings
            warnings.simplefilter("ignore")

    def test_hca2scea_characteristic(self):
        # run tool
        arguments_df = pd.read_csv("test/golden/arguments.csv")
        for i in range(0,arguments_df.shape[0]):
            spreadsheet = "test/golden/" + list(arguments_df['spreadsheet'])[i]
            with self.subTest(spreadsheet="test/golden/" + list(arguments_df['spreadsheet'])[i]):
                arguments = arguments_df.loc[arguments_df['spreadsheet'] == os.path.basename(spreadsheet)]
                output_dir = self.run_tool(spreadsheet, arguments)
                self.check_output(output_dir, spreadsheet)

    def get_file_content(self, file):
        if file.split(".")[-1] == 'csv' or file.split(".")[-2] == 'sdrf':
            file_contents = pd.read_csv(file, sep='\t')
        else:
            file_contents = open(file).read()
        return file_contents

    def check_equal_df(self, golden_contents, output_contents):
        assert_frame_equal(golden_contents, output_contents)

    def check_equal_lines(self, golden_contents, output_contents):
        self.assertMultiLineEqual(golden_contents,output_contents)

    def check_output(self, output_dir, spreadsheet):
        golden_output_dir = 'test/golden/output/' + os.path.basename(spreadsheet).split(".xlsx")[0]
        for golden_file in os.listdir(golden_output_dir):
            output_file = os.path.join(output_dir, os.path.basename(golden_file))
            golden_contents = self.get_file_content(os.path.join(golden_output_dir, os.path.basename(golden_file)))
            output_contents = self.get_file_content(output_file)
            if isinstance(golden_contents, pd.DataFrame):
                self.check_equal_df(golden_contents, output_contents)
            else:
                self.check_equal_lines(golden_contents, output_contents)

    def run_tool(self, spreadsheet, arguments):
        output_name = os.path.basename(spreadsheet).split(".xlsx")[0]
        output_dir = 'output/' + output_name
        arguments = arguments.reset_index()
        os.system(
            f'python3 script.py -s {spreadsheet} -o {output_dir} -id {arguments["HCA project uuid"][0]} -ac {arguments["E-HCAD accession"][0]} -c {arguments["curator initials"][0]} -tt {arguments["technology"][0]} -et {arguments["experiment type"][0]} -f {arguments["factor values"][0]} -pd {arguments["public release date"][0]} -hd {arguments["hca last update date"][0]} -study {arguments["study accession"][0]}')
        return output_dir

if __name__ == '__main__':
    unittest.main()
