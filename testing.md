# Running the tests

```bash
python -m unittest
```

# Test data
Test data consists of HCA spreadsheets and the matching SCEA files (idf, sdrf) that should be generated for them.

The test cases to run are written in the arguments.csv file.

Each row contains the data for one test case:
* spreadsheet
* HCA project uuid
* E-HCAD accession
* curator initials
* technology - from tracker sheet
* experiment type - we do collect it in the dataset tracking sheet
* [factor values](https://www.ebi.ac.uk/gxa/sc/experiments?species=%22homo+sapiens%22&experimentProjects=%22Human+Cell+Atlas%22) - a bit more complicated, it's basically the
  "scientific comparison variables" of each experiment (e.g. if they sample the same type of tissue on healthy young, young adult 
  and adult people the factor value is age, since they are studying the effect of age on the tissue).
* public release date -  from each of the accessions
* hca last update date - the hca last update date can be extracted from ingest
* study accession - we collect it under accessions
