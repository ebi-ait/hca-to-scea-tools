# HCA-TO-SCEA Tools

This repo contains various tools to help on the task of converting HCA spreadsheets to SCEA magetab files.

## hca2scea tool

### Installation

Prerequisites: [npm](https://www.npmjs.com/), [pip](https://pypi.org/project/pip/) and the _pip_ package [virtualenv](https://virtualenv.pypa.io/en/latest/).

Once those are ready, to install the application run:

```
cd hca2scea-backend
./install.sh
```

## Execution

In the same hca2scea-backend directory, run:

```
npm start
```

And then, head to [http://127.0.0.1:5000]() on a browser.

Once run, the application will save the `idf` and `sdrf` parts of the magetab, along with any intermediate files used in the process into the folder `./hca2scea-backend/spreadsheets/<spreadsheet_name>/`.


## Column mapping

This table shows the source of the columns generated in the MAGE-TAB file.

| Column in MAGE-TAB SDRF file              | Source                   | Description                                                               | Default      |
|-------------------------------------------|--------------------------|---------------------------------------------------------------------------|--------------|
|`Source Name`                              | Selectable from          | Any column ending with `biomaterial_id` or `biosamples_accession`         |              |
|`Characteristics[organism]`                | Column                   | `donor_organism.genus_species.ontology_label`                             |              |
|`Characteristics[individual]`              | Column                   | `donor_organism.biomaterial_core.biomaterial_id`                          |              |
|`Characteristics[sex]`                     | Column                   | `donor_organism.sex`                                                      |              |
|`Characteristics[age]`                     | Column                   | `donor_organism.organism_age`                                             |              |
|`Unit [time unit]`                         | Column                   | `donor_organism.organism_age_unit.text`                                   |              |
|`Characteristics[developmental stage]`     | Column                   | `donor_organism.development_stage.text`                                   |              |
|`Characteristics[organism part]`           | Column                   | `specimen_from_organism.organ.ontology_label`                             |              |
|`Characteristics[sampling site]`           | Column                   | `specimen_from_organism.organ_parts.ontology_label`                       |              |
|`Characteristics[cell type]`               | Column                   | `cell_suspension.selected_cell_types.ontology_label`                      |              |
|`Characteristics[disease]`                 | Column                   | `donor_organism.diseases.ontology_label`                                  |              |
|`Characteristics[organism status]`         | Column                   | `donor_organism.is_living`                                                |              |
|`Characteristics[cause of death]`          | Column                   | `donor_organism.death.cause_of_death`                                     |              |
|`Characteristics[clinical history]`        | Column                   | `donor_organism.medical_history.test_results`                             |              |
|`Description`                              | Column                   | `specimen_from_organism.biomaterial_core.biomaterial_description`         |              |
|`Material Type` (first instance)           | Fill cells with one of   | `whole organism`, `organism part`, `cell`                                 |              |
|`Protocol REF` (first group of instances)  | Special protocol columns | Includes collection/dissociation/enrichment/library prep protocols        |              |
|`Extract Name`                             | Selectable from          | Any column ending with `biomaterial_id` or `biosamples_accession`         |              |
|`Material Type` (second instance)          | Fill cells with value    | `RNA`                                                                     |              |
|`Comment[library construction]`            | Column                   | `library_preparation_protocol.library_construction_method.ontology_label` |              |
|`Comment[input molecule]`                  | Column                   | `library_preparation_protocol.input_nucleic_acid_molecule.ontology_label` |              |
|`Comment[primer]`                          | Fill cells with value    | `oligo-DT`                                                                |              |
|`Comment[end bias]`                        | Column                   | `library_preparation_protocol.end_bias`                                   |              |
|`Comment[umi barcode read]`                | Column or default        | `library_preparation_protocol.umi_barcode.barcode_read`                   | `read1`      |
|`Comment[umi barcode offset]`              | Column or default        | `library_preparation_protocol.umi_barcode.barcode_offset`                 | `16`         |
|`Comment[umi barcode size]`                | Column or default        | `library_preparation_protocol.umi_barcode.barcode_length`                 | `10`         |
|`Comment[cell barcode read]`               | Column or default        | `library_preparation_protocol.cell_barcode.barcode_read`                  | `read1`      |
|`Comment[cell barcode offset]`             | Column or default        | `library_preparation_protocol.cell_barcode.barcode_offset`                | `0`          |
|`Comment[cell barcode size]`               | Column or default        | `library_preparation_protocol.cell_barcode.barcode_length`                | `16`         |
|`Comment[sample barcode read]`             | Empty                    |                                                                           |              |
|`Comment[sample barcode offset]`           | Fill cells with value    | `0`                                                                       |              |
|`Comment[sample barcode size]`             | Fill cells with value    | `8`                                                                       |              |
|`Comment[single cell isolation]`           | Fill cells with value    | `magnetic affinity cell sorting`                                          |              |
|`Comment[cDNA read]`                       | Fill cells with value    | `read2`                                                                   |              |
|`Comment[cDNA read offset]`                | Fill cells with value    | `0`                                                                       |              |
|`Comment[cDNA read size]`                  | Fill cells with value    | `98`                                                                      |              |
|`Comment[LIBRARY_STRAND]`                  | Column                   | `library_preparation_protocol.strand`                                     |              |
|`Comment[LIBRARY\_LAYOUT]`                 | Fill cells with value    | `PAIRED`                                                                  |              |
|`Comment[LIBRARY\_SOURCE]`                 | Fill cells with value    | `TRANSCRIPTOMIC SINGLE CELL`                                              |              |
|`Comment[LIBRARY\_STRATEGY]`               | Fill cells with value    | `RNA-Seq`                                                                 |              |
|`Comment[LIBRARY\_SELECTION]`              | Fill cells with value    | `cDNA`                                                                    |              |
|`Protocol REF (second group of instances)  | Special protocol columns | Includes sequencing protocol                                              |              |
|`Assay Name`                               | Column                   | `specimen_from_organism.biomaterial_core.biomaterial_id`                  |              |
|`Technology Type`                          | Fill cells with value    | `sequencing assay`                                                        |              |
|`Scan Name`                                | Selectable from          | Any column ending with `biomaterial_id` or `biosamples_accession`         |              |
|`Comment[RUN]`                             | Selectable from          | Any column ending with `biomaterial_id` or `biosamples_accession`         |              |
|`Comment[read1 file]`                      | Column                   | `sequence_file.file_core.file_name_read1`                                 |              |
|`Comment[read2 file]`                      | Column                   | `sequence_file.file_core.file_name_read2`                                 |              |
|`Comment[index1 file]`                     | Column                   | `sequence_file.file_core.file_name_index`                                 |              |
