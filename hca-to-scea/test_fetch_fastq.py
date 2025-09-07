import unittest
from unittest.mock import patch, MagicMock
import pandas as pd

import helpers.fetch_fastq_path as fetch_fastq_path


class TestSraUtils(unittest.TestCase):

    def test_sort_fastq_with_r1_r2(self):
        paths = {
            "SRR123": {"files": ["sample_R1.fastq.gz", "sample_R2.fastq.gz"]}
        }
        result = fetch_fastq_path.sort_fastq(paths)

        self.assertIn("SRR123", result)
        self.assertEqual(result["SRR123"]["filename_read1"], "sample_R1.fastq.gz")
        self.assertEqual(result["SRR123"]["filename_read2"], "sample_R2.fastq.gz")
        self.assertEqual(result["SRR123"]["filetype"], "fastq file")

    def test_filter_paths_fastq(self):
        sdrf = pd.DataFrame({"Comment[ENA_RUN]": ["SRR123"]})
        paths = {
            "SRR123": {
                "filetype": "fastq file",
                "filename_read1": "R1.fastq.gz",
                "filepath_read1": "ftp://example/R1.fastq.gz",
                "filename_read2": "R2.fastq.gz",
                "filepath_read2": "ftp://example/R2.fastq.gz",
            }
        }

        result = fetch_fastq_path.filter_paths(sdrf.copy(), paths)

        self.assertIn("Comment[read1 file]", result.columns)
        self.assertEqual(result["Comment[read1 file]"].iloc[0], "R1.fastq.gz")
        self.assertEqual(result["Comment[read2 file]"].iloc[0], "R2.fastq.gz")

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
