import os
import sys
import unittest
import pandas as pd
import json
import glob

# TODO: add input/output pairs - more test scenarios

class CharacteristicTest(unittest.TestCase):

    def setUp(self):
        self.verificationErrors = {}
        if not sys.warnoptions:
            import warnings
            warnings.simplefilter("ignore")

    def test_hca2scea_characteristic(self):
        # run tool
        spreadsheets = glob.glob("test/golden/*.xlsx")
        arguments_df = pd.read_csv("test/golden/arguments.txt", sep="\t")
        for spreadsheet in spreadsheets:
            arguments = arguments_df.loc[arguments_df['spreadsheet'] == os.path.basename(spreadsheet)]
            output_dir = self.run_tool(spreadsheet, arguments)
            self.check_output(output_dir, spreadsheet)
        with open("test_errors.json", "w") as out_file:
            json.dump(self.verificationErrors, out_file)

    def get_content(self, golden_file, output_file):
        if golden_file.split(".")[-1] == 'csv' or golden_file.split(".")[-2] == 'sdrf':
            golden_contents = pd.read_csv(golden_file, sep='\t')
            output_contents = pd.read_csv(output_file, sep='\t')
        else:
            golden_contents = open(golden_file).readlines()
            output_contents = open(output_file).readlines()
        return golden_contents, output_contents

    def check_equal_df(self, golden_contents, output_contents, spreadsheet, output_file):
        bool = golden_contents.equals(output_contents)
        try:
            self.assertTrue(bool)
            return True
        except AssertionError:
            if spreadsheet not in self.verificationErrors.keys():
                self.verificationErrors[spreadsheet] = {output_file: []}
            return False

    def check_equal_lines(self, golden_contents, output_contents, spreadsheet, output_file):
        try:
            self.assertEqual(golden_contents,output_contents)
            return False
        except AssertionError:
            if spreadsheet not in self.verificationErrors.keys():
                self.verificationErrors[spreadsheet] = {output_file: []}
            return False

    def get_diff(self, golden_contents, output_contents, spreadsheet, output_file):
        if isinstance(output_contents,pd.DataFrame):
            output_contents = output_contents.values.tolist()
            golden_contents = golden_contents.values.tolist()
        for line_number in range(0,len(output_contents)):
            if output_contents[line_number] != golden_contents[line_number]:
                self.verificationErrors[spreadsheet][output_file].append(line_number)

    def check_output(self, output_dir, spreadsheet):
        golden_output_dir = 'test/golden/output/' + os.path.basename(spreadsheet).split(".xlsx")[0]
        for golden_file in os.listdir(golden_output_dir):
            output_file = os.path.join(output_dir, os.path.basename(golden_file))
            golden_contents, output_contents = self.get_content(os.path.join(golden_output_dir, os.path.basename(golden_file)), output_file)
            if isinstance(golden_contents, pd.DataFrame):
                equal = self.check_equal_df(golden_contents, output_contents, spreadsheet, output_file)
            else:
                equal = self.check_equal_lines(golden_contents, output_contents, spreadsheet, output_file)
            if equal is False:
                self.get_diff(golden_contents, output_contents, spreadsheet, output_file)

    def run_tool(self, spreadsheet, arguments):
        output_name = os.path.basename(spreadsheet).split(".xlsx")[0]
        output_dir = 'output/' + output_name
        print(arguments)
        os.system(
            f'python3 script.py -s {spreadsheet} -o {output_dir} -id {arguments["HCA project uuid"][0]} -ac {arguments["E-HCAD accession"][0]} -c {arguments["curator initials"][0]} -tt {arguments["technology"][0]} -et {arguments["experiment type"][0]} -f {arguments["factor values"][0]} -pd {arguments["public release date"][0]} -hd {arguments["hca last update date"][0]} -study {arguments["study accession"][0]}')
        return output_dir

if __name__ == '__main__':
    unittest.main()
