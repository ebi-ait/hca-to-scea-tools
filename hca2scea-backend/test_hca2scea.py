import os
import sys
import unittest
import pandas as pd
import json

# TODO: add input/output pairs - more test scenarios

class CharacteristicTest(unittest.TestCase):

    def setUp(self):
        self.verificationErrors = {}
        if not sys.warnoptions:
            import warnings
            warnings.simplefilter("ignore")

    def test_hca2scea_characteristic(self):
        # run tool
        spreadsheet = 'test/golden/' + 'GSE148963_final_scea.xlsx'
        output_dir = self.run_tool(spreadsheet)
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
        golden_output_dir = 'test/golden/output'
        for golden_file in os.listdir(golden_output_dir):
            output_file = os.path.join(output_dir, os.path.basename(golden_file))
            golden_contents, output_contents = self.get_content(os.path.join(golden_output_dir, os.path.basename(golden_file)), output_file)
            if isinstance(golden_contents, pd.DataFrame):
                equal = self.check_equal_df(golden_contents, output_contents, spreadsheet, output_file)
                print(equal)
            else:
                equal = self.check_equal_lines(golden_contents, output_contents, spreadsheet, output_file)
                print(equal)
            if equal is False:
                self.get_diff(golden_contents, output_contents, spreadsheet, output_file)

    def run_tool(self, spreadsheet):
        output_dir = 'output'
        os.system(
            f'python3 script.py -s {spreadsheet} -o {output_dir} -id c893cb57-5c9f-4f26-9312-21b85be84313 -ac E-HCAD-50 -c AD -tt 10Xv2_3 -et baseline -f individual -pd 2009-02-27 -hd 2021-04-29 -study SRP257542')
        return output_dir

if __name__ == '__main__':
    unittest.main()
