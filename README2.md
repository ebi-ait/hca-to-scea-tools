## hca_to_scea
A tool to assist in the automatic conversion of an hca metadata spreadsheet to scea metadata MAGE-TAB files.

## Installation

    pip install hca-to-scea
    
## Description

The tool takes as input an HCA metadata spreadsheet and converts the metadata to SCEA MAGE-TAB files which are then saved to an output directory.

## Usage

To run it as a package, after installing it via pip:


```shell script
$ hca-to-scea -h                                                  
usage: hca2scea.py [-h] -s SPREADSHEET -id PROJECT_UUID -study STUDY
                   [-name {cs_name,cs_id,sp_name,sp_id,other}] -ac
                   ACCESSION_NUMBER -c CURATORS [CURATORS ...] -tt
                   {10Xv1_3,10Xv2_3,10Xv2_5,10Xv3_3,drop-seq,smart-seq,seq-well,smart-like}
                   -et {baseline,differential} [--facs] -f
                   EXPERIMENTAL_FACTORS [EXPERIMENTAL_FACTORS ...] -pd
                   PUBLIC_RELEASE_DATE -hd HCA_UPDATE_DATE
                   [-r RELATED_SCEA_ACCESSION [RELATED_SCEA_ACCESSION ...]]
                   [-o OUTPUT_DIR]

run hca -> scea tool

optional arguments:
  -h, --help            show this help message and exit
  -s SPREADSHEET, --spreadsheet SPREADSHEET
                        Please provide a path to the HCA project spreadsheet.
  -id PROJECT_UUID, --project_uuid PROJECT_UUID
                        Please provide an HCA ingest project submission id.
  -study STUDY          Please provide the SRA or ENA study accession.
  -name {cs_name,cs_id,sp_name,sp_id,other}
                        Please indicate which field to use as the sample name.
                        cs=cell suspension, sp = specimen.
  -ac ACCESSION_NUMBER, --accession_number ACCESSION_NUMBER
                        Provide an E-HCAD accession number. Please find the
                        next suitable accession number by checking the google
                        tracker sheet.
  -c CURATORS [CURATORS ...], --curators CURATORS [CURATORS ...]
                        space separated names of curators
  -tt {10Xv1_3,10Xv2_3,10Xv2_5,10Xv3_3,drop-seq,smart-seq,seq-well,smart-like}, --technology_type {10Xv1_3,10Xv2_3,10Xv2_5,10Xv3_3,drop-seq,smart-seq,seq-well,smart-like}
                        Please indicate which single-cell sequencing
                        technology was used.
  -et {baseline,differential}, --experiment_type {baseline,differential}
                        Please indicate whether this is a baseline or
                        differential experimental design
  --facs                Please specify this argument if FACS was used to
                        isolate single cells
  -f EXPERIMENTAL_FACTORS [EXPERIMENTAL_FACTORS ...], --experimental_factors EXPERIMENTAL_FACTORS [EXPERIMENTAL_FACTORS ...]
                        space separated list of experimental factors
  -pd PUBLIC_RELEASE_DATE, --public_release_date PUBLIC_RELEASE_DATE
                        Please enter the public release date in this format:
                        YYYY-MM-DD
  -hd HCA_UPDATE_DATE, --hca_update_date HCA_UPDATE_DATE
                        Please enter the last time the HCA prohect submission
                        was updated in this format: YYYY-MM-DD
  -r RELATED_SCEA_ACCESSION [RELATED_SCEA_ACCESSION ...], --related_scea_accession RELATED_SCEA_ACCESSION [RELATED_SCEA_ACCESSION ...]
                        space separated list of related scea accession(s)
  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Provide full path to preferred output dir
```

To run it as a python module:

```shell script 
cd /path-to/hca_to_scea
python -m hca-to-scea-tools.hca2scea-backend.hca2scea -h
```

### Table

**Arguments explained**

| Argument   | Argument name            | Description                                                                                        | Required? |
|------------|--------------------------|----------------------------------------------------------------------------------------------------|-----------|
|-s          | HCA spreadsheet          | Path to HCA spreadsheet (.xlsx)                                                                    | yes       |
|-id         | HCA project uuid         | This is added to the 'secondary accessions' field in idf file                                      | yes       | 
|-c          | Curator initials         | HCA Curator initials. Space-separated list.                                                        | yes       |
|-ac         | accession number         | Provide an SCEA accession number (integer).                                                        | yes       |
|-tt         | Technology type          | Must be [10Xv2_3,10Xv2_5,10Xv3_3,10Xv3_5,drop-seq,smart-seq,seq-well,smart-like]                   | yes       |
|-et         | Experiment type          | Must be 1 of [differential,baseline]                                                               | yes       |
|-f          | Factor value             | A space-separated list of user-defined factor values e.g. age disease                              | yes       |
|-pd         | Dataset publication date | provide in YYYY-MM-DD E.g. from GEO                                                                | yes       |
|-hd         | HCA last update date     | provide in YYYY-MM-DD The last time the HCA project was updated in ingest  UI (production)         | yes       |
|-r          | Related E-HCAD-id        | If there is a related project, you should enter the related E-HCAD-id here e.g.['E-HCAD-39']       | no        |
|-study      | study accession (SRPxxx) | The study accession will be used to find the paths to the fastq files for the given runs           | yes       |
|-name       | HCA name field           | Which HCA field to use for the biomaterial names columns. Must be 1 of                             | no        |
|            |                          | [cs_name, cs_id, sp_name, sp_id, other] where cs indicates cell suspension and sp indicates        |           |
|            |                          |  specimen from organism. Default is cs_name.                                                       |           |
|--facs      | optional argument        | If FACS was used as a single cell isolation method, indicate this by adding the --facs argument.   | no        |
|-o          | optional argument        | An output dir path can optionally be provided. If it does not exist, it will be created.           | no        |

**Example commands**

Required arguments only

`python3 hca2scea.py -s /home/aday/GSE111976-endometrium_MC_SCEA.xlsx -id 379ed69e-be05-48bc-af5e-a7fc589709bf -study SRP135922 -ac 50 -c AD -tt 10Xv3_3 -et differential -f menstrual cycle day -pd 2021-06-29 -hd 2021-02-12`


Specify optional name argument

`python3 hca2scea.py -s /home/aday/GSE111976-endometrium_MC_SCEA.xlsx -id 379ed69e-be05-48bc-af5e-a7fc589709bf -study SRP135922 -name cs_name -ac 50 -c AD -tt 10Xv3_3 -et differential -f menstrual cycle day -pd 2021-06-29 -hd 2021-02-12`

Specify optional related scea accession

`python3 hca2scea.py -s /home/aday/GSE111976-endometrium_MC_SCEA.xlsx -id 379ed69e-be05-48bc-af5e-a7fc589709bf -study SRP135922 -ac 50 -c AD -tt 10Xv3_3 -et differential -f menstrual cycle day -pd 2021-06-29 -hd 2021-02-12 -r 51`


Specify that FACS was used

`python3 hca2scea.py -s /home/aday/GSE111976-endometrium_MC_SCEA.xlsx -id 379ed69e-be05-48bc-af5e-a7fc589709bf -study SRP135922 -ac 50 -c AD -tt 10Xv3_3 -et differential -f menstrual cycle day -pd 2021-06-29 -hd 2021-02-12 --facs`


Specify optional output dir

`python3 hca2scea.py -s /home/aday/GSE111976-endometrium_MC_SCEA.xlsx -id 379ed69e-be05-48bc-af5e-a7fc589709bf -study SRP135922 -ac 50 -c AD -tt 10Xv3_3 -et differential -f menstrual cycle day -pd 2021-06-29 -hd 2021-02-12 -o my_output_dir`

#### Definitions ####

**Experiment type**

An experiment with samples which can be grouped or differentiatied by a factor value is classified as 'differential'. Baseline indicates an experiment with no clear grouping or factor value.

*Example differential*

normal and disease, multiple developmental stages

*Example baseline*

all primary samples from 1 organ type and same developmental stage and disease status.

**Factor values**

A factor value is a chosen experimental characteristic which can be used to group or differentiate samples. If there is no obvious factor value, 1 must be given. In this case, you can add 'individual', which indicates the unique donors. The SCEA team's validator tools will fail without this.

Technology cannot be a factor value.

*Example:*

individual, disease, developmental stage, age

A list of example factor values that could be used has also been provided by the scea team here: https://docs.google.com/spreadsheets/d/1NQ5c7eqaFHnIC7e359ID5jtSawyOcnyv/edit#gid=1742687040

**Related E-HCAD-ID**

If the project has been split into two separate E-HCAD datasets, due to different technologies being used in the same project, or any other reason, then enter the E-HCAD-ID for the other dataset here.

*Example*

E-HCAD-34

## Developer Notes

### Developing Code in Editable Mode

Using `pip`'s editable mode, projects using hca-to-scea as a dependency can refer to the latest code in this repository 
directly without installing it through PyPI. This can be done either by manually cloning the code
base:

    pip install -e path/to/hca-to-scea

or by having `pip` do it automatically by providing a reference to this repository:

    pip install -e \
    git+https://github.com/ebi-ait/hca-to-scea-tools.git\
    #egg=hca-to-scea
    
    
### Publish to PyPI

1. Create PyPI Account through the [registration page](https://pypi.org/account/register/).
    
   Take note that PyPI requires email addresses to be verified before publishing.

2. Package the project for distribution.
 
        python setup.py sdist
    
3. Install [Twine](https://pypi.org/project/twine/)

        pip install twine        
    
4. Upload the distribution package to PyPI. 

        twine upload dist/*
        
    Running `python setup.py sdist` will create a package in the `dist` directory of the project
    base directory. 
    


