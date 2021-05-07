import os
import unittest

# TODO: print actual different lines rather than just the fact that there is a difference
# TODO: add input/output pairs - more test scenarios

class CharacteristicTest(unittest.TestCase):
    def test_hca2scea_characteristic(self):
        # run tool
        spreadsheet = 'test/golden/' + 'GSE148963_final_scea.xlsx'
        output_dir = self.run_tool(spreadsheet)
        self.check_output(output_dir, spreadsheet)

    def check_output(self, output_dir, spreadsheet):
        golden_output_dir = 'test/golden/output'
        for golden_file in os.listdir(golden_output_dir):
            output_file = os.path.join(output_dir, os.path.basename(golden_file))
            golden_contents = open(os.path.join(golden_output_dir, golden_file)).read()
            output_contents = open(output_file).read()
            self.assertEqual(golden_contents,
                             output_contents,
                             f'problem in file {output_file} from spreadsheet {spreadsheet}')

    def run_tool(self, spreadsheet):
        output_dir = 'output'
        os.system(
            f'python3 script.py -s {spreadsheet} -o {output_dir} -id c893cb57-5c9f-4f26-9312-21b85be84313 -ac E-HCAD-50 -c AD -tt 10Xv2_3 -et baseline -f individual -pd 2009-02-27 -hd 2021-04-29 -study SRP257542')
        return output_dir


if __name__ == '__main__':
    unittest.main()
