import unittest
from unittest.mock import patch, MagicMock
import pandas as pd

import helpers.fetch_fastq_path as fetch_fastq_path


class TestSraUtils(unittest.TestCase):

    @patch("helpers.fetch_fastq_path.rq.get")
    def test_retrieve_xml_from_sra(self, mock_get):
        fake_xml = """
        <ROOT>
          <EXPERIMENT_PACKAGE>
            <RUN_SET>
              <RUN accession="SRR123456">
                <SRAFiles>
                  <SRAFile sratoolkit="1" filename="SRR123456" url="ftp://example.org/SRR123456.sra"/>
                </SRAFiles>
              </RUN>
            </RUN_SET>
          </EXPERIMENT_PACKAGE>
        </ROOT>
        """
        mock_resp = MagicMock()
        mock_resp.content = fake_xml.encode()
        mock_get.return_value = mock_resp

        result = fetch_fastq_path.retrieve_xml_from_sra(["SRR123456"])

        self.assertIn("SRR123456", result)
        self.assertIn("ftp://example.org/SRR123456.sra", result["SRR123456"]["files"])

    @patch("helpers.fetch_fastq_path.pd.read_csv")
    def test_get_fastq_path_from_ena(self, mock_read_csv):
        fake_df = pd.DataFrame({
            "run_accession": ["SRR111"],
            "fastq_ftp": ["ftp.sra.ebi.ac.uk/file1.fastq.gz;ftp.sra.ebi.ac.uk/file2.fastq.gz"]
        })
        mock_read_csv.return_value = fake_df

        result = fetch_fastq_path.get_fastq_path_from_ena(["SRR111"])

        self.assertIn("SRR111", result)
        self.assertEqual(len(result["SRR111"]["files"]), 2)
        self.assertTrue(result["SRR111"]["files"][0].startswith("ftp://"))


if __name__ == "__main__":
    unittest.main()
