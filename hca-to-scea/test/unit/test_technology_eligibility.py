import unittest

class TestTechnologyIsEligible(unittest.TestCase):

    def setUp(self):
        # Load test data
        basic_spreadsheet = pd.ExcelFile("../golden/hca_to_scea_test_01.xlsx", engine='openpyxl')
        self.spreadsheet = pd.read_excel(
            basic_spreadsheet,
            sheet_name="Library preparation protocol",
            header=0,
            skiprows=[0, 1, 2, 4],
            engine='openpyxl')

    def test_technology_type(self):
        technology_type_list = self.spreadsheet.get_technology_list()
        message = "Technology type %s is not in list of eligible technologies." % (technology_type)
        self.assertIn(technology_type, technology_dict, message)

if __name__ == '__main__':
    unittest.main()