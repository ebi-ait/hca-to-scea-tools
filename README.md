# HCA-TO-SCEA Tools

This repo contains various tools to help on the task of converting HCA spreadsheets to SCEA magetab files.

## SCEA eligibility criteria
See [docs/eligibility.md]

## Running the hca2scea tool

### Installation

The hca-to-scea tool is installed on EC2. If you're a new team member and you need access to EC2 or permissions to run the tool, please speak with Amnon, our technical coordinator, or another HCA developer.
The tool is installed automatically after a successful build. See the github actions.

### Copying your HCA spreadsheet to EC2

In order to use the hca-to-scea tool on EC2, you will need to copy your input HCA spreadsheet there, for example in your home folder. An example command to do this:

```bash
scp -i [OPENSSH PRIVATE KEY file path] [path to spreadsheet] [username]@tool.archive.data.humancellatlas.org:/home/[username]
```

### Setting the environment on EC2

Go to the hca-to-scea-tools directory and activate the environment.
```bash
cd /data/tools/hca-to-scea-tools/hca2scea-backend
source venv/bin/activate
```

### Running the tool on EC2

#### Command-line ####

The easiest way might be to copy the example below, and replace the arguments as necessary whilst referring to this readme.

```bash
python3 hca2scea.py -s [spreadsheet (xlsx)] -id [hca project uuid] -study [study accession (SRPxxx)] -name {cs_name,cs_id,sp_name,sp_id,other} -ac [accession number] -c [curator initials] -tt [technology type] -et [experiment type] -f [factor values] -pd [dataset publication date] -hd [hca last update date] -r [related scea accession] --facs -o [output dir]
```

**Examples**

**Required arguments only**
```bash
python3 hca2scea.py -s /home/aday/GSE111976-endometrium_MC_SCEA.xlsx -id 379ed69e-be05-48bc-af5e-a7fc589709bf -study SRP135922 -ac 50 -c AD -tt 10Xv3_3 -et differential -f menstrual cycle day -pd 2021-06-29 -hd 2021-02-12
```

**Specify optional name argument**
```
python3 hca2scea.py -s /home/aday/GSE111976-endometrium_MC_SCEA.xlsx -id 379ed69e-be05-48bc-af5e-a7fc589709bf -study SRP135922 -name cs_name -ac 50 -c AD -tt 10Xv3_3 -et differential -f menstrual cycle day -pd 2021-06-29 -hd 2021-02-12
```

**Specify optional related scea accession**
```
python3 hca2scea.py -s /home/aday/GSE111976-endometrium_MC_SCEA.xlsx -id 379ed69e-be05-48bc-af5e-a7fc589709bf -study SRP135922 -ac 50 -c AD -tt 10Xv3_3 -et differential -f menstrual cycle day -pd 2021-06-29 -hd 2021-02-12 -r 51
```

**Specify that FACS was used**
```
python3 hca2scea.py -s /home/aday/GSE111976-endometrium_MC_SCEA.xlsx -id 379ed69e-be05-48bc-af5e-a7fc589709bf -study SRP135922 -ac 50 -c AD -tt 10Xv3_3 -et differential -f menstrual cycle day -pd 2021-06-29 -hd 2021-02-12 --facs
```

**Specify optional output dir**
```
python3 hca2scea.py -s /home/aday/GSE111976-endometrium_MC_SCEA.xlsx -id 379ed69e-be05-48bc-af5e-a7fc589709bf -study SRP135922 -ac 50 -c AD -tt 10Xv3_3 -et differential -f menstrual cycle day -pd 2021-06-29 -hd 2021-02-12 -o my_output_dir
```

#### Arguments ####

**How to choose an E-HCAD accession number**

Please check the [tracker sheet](https://docs.google.com/spreadsheets/d/1rm5NZQjE-9rZ2YmK_HwjW-LgvFTTLs7Q6MzHbhPftRE/edit#gid=0) for the next suitable E-HCAD accession number. Please ensure the E-HCAD id you choose is unique and not already present in the tracker sheet. It should be the next consecutive number after the maximum number in the sheet.

It is also a good idea to notify in hca-wrangler-metadata that you are doing some SCEA wrangling to ensure the E-HCAD-id does not get duplicated. The accession is a required argument for the script.

*Example*

If accessions E-HCAD1 to E-HCAD32 have already been assigned to datasets, the next accession number would be 33.

**Arguments table**

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

#### Definitions ####

**Experiment type**

An experiment with samples which can be grouped or differentiatied by a factor value is classified as 'differential'. Baseline indicates an experiment with no clear grouping or factor value.

*Example differential*

normal and disease, multiple developmental stages

*Example baseline*

all primary samples from 1 organ type and same developmental stage and disease status.

**Factor values**

A factor value is a chosen experimental characteristic which can be used to group or differentiate samples. **If there is no obvious factor value, 1 must be given. In this case, you can add 'individual', which indicates the unique donors.** The SCEA team's validator tools will fail without this.

Technology cannot be a factor value.

*Example:*

individual, disease, developmental stage, age

A list of example factor values that could be used has also been provided by the scea team here: https://docs.google.com/spreadsheets/d/1NQ5c7eqaFHnIC7e359ID5jtSawyOcnyv/edit#gid=1742687040

**Related E-HCAD-ID**

If the project has been split into two separate E-HCAD datasets, due to different technologies being used in the same project, or any other reason, then enter the E-HCAD-ID for the other dataset here.

*Example*

E-HCAD-34

#### Output ####

The script will output an idf file and an sdrf file named with the same new E-HCAD-id. These files will be written into a new folder: `./hca2scea-backend/script_spreadsheets/<spreadsheet_name>/`.

You will then need to copy them to your local desktop to further manually curate them. Please delete the folder from the above directory once you have done this. An example command to do this is below. It must be run from the terminal on your local desktop, not from inside EC2:

```
scp -i [OPENSSH PRIVATE KEY file path] [username]@tool.archive.data.humancellatlas.org:/home/tools/hca-to-scea-tools/hca2scea-backend/script_spreadsheets/[your output dir] [local folder path] 
```

Alternatively, see [here](https://ebi-ait.github.io/hca-ebi-wrangler-central/tools/handy_snippets.html#transfer-files-between-local-machine-and-ec2-scp-rsync) for tips on how to do this.

## Record assigned E-HCAD ID ##

At this point you should enter the newly assigned E-HCAD id(s) (e.g. E-HCAD-33) into the [tracker sheet](https://docs.google.com/spreadsheets/d/1rm5NZQjE-9rZ2YmK_HwjW-LgvFTTLs7Q6MzHbhPftRE/edit#gid=0). Please enter in all relevent accession columns to make sure they are visible to other wranglers when they select the next E-HCAD accession number for their dataset.

Please also note the E-HCAD id in the dataset ticket in the HCA Dataset Wrangling Zenhub board and manage the SCEA curation status of your dataset using the SCEA wrangling Zenhub board.

## Manually curate the output ##

Some curation is required to be done manually. These steps will be automated as we develop the tool, where possible.

If you get stuck, it might be worth first looking [here](https://github.com/ebi-ait/hca-to-scea-tools/tree/master/example_output) for examples of idf and sdrf files as a guide.

### Update idf file ###

Additional fields that are not yet automated by the hca2sceal tool are:

- Comment[EAAdditionalAttributes]

You should add a tab separated list of key variables of interest for display in the SCEA visualisation tool.
Add 'individual', 'sex' and 'age' if these columns are filled in the sdrf file.
If 'sex' or 'age' are empty columns, add only 'individual'.

Examples:

Comment[EAAdditionalAttributes] individual  sex age
Comment[EAAdditionalAttributes] individual

- Publication fields (I am working on adding this to the script, ignore this for now)

### Check idf format ###

#### File format ####

The following should be separated by a tab:

 - a field name and corresponding value(s)
 - values in a list of values
 - empty values in a list

The following should be separated by a space

 - multiple words within a single string

*Example1*

Protocol[space]Type[space]sample[tab]collection[space]protocol[tab]sample[space]collection[space]protocol

*Example2:*

Person First Name[tab][author1 first name][tab][author2 first name][tab][author3 first name][tab][author4 first name]
Person Email[tab][author1 email][tab][author2 email][tab][tab][author4 email]

Check that there is no extra white space (empty lines) at the end of the file. This will cause validation errors.

#### Valid Protocol Types ####

Valid protocol types are:

sample collection protocol, enrichment protocol, growth protocol, treatment protocol, nucleic acid library construction protocol, nucleic acid sequencing protocol

Hca2scea Protocol type map:

| HCA Protocol Type                 | SCEA Protocol Type                         |
|-----------------------------------|--------------------------------------------|
| Collection protocol               | sample collection protocol                 |
| Dissociation protocol             | enrichment protocol                        |
| Enrichment protocol               | enrichment protocol                        |
| Differentiation protocol          | growth protocol                            |
| unspecified                       | treatment protocol                         |
| Library preparation protocol      | nucleic acid library construction protocol |
| Sequencing protocol               | nucleic acid sequencing protocol           |

#### Protocol Type format ####

- The protocol Name should be ordered by number
- The protocol Type and Description order must reflect the Name order
- Aim to simplify every protocol description to no more than 2 sentences. The SCEA team prefer the protocols have general and short descriptions with less extensive detail

### Update sdrf file ###

Additional fields that are not yet automated by the hca2sceal tool are:

- Factor Values. You will need to add new factor value columns to the file. These should be the last column(s) in the table. The columns should be filled with the factor value(s) that you selected earlier *(See above for the Definition of "Factor Value")*.
- The factor value column names should be "Factor Value[column name]", where the column name is the selected Factor value of interest.

*Example:*

"Factor Value[disease]"
"Factor Value[sampling site]"

### Check sdrf format ###

#### File paths ####

We do not need to send raw data files to SCEA. The script will try to automatically enter fastq file paths for each given run accession in the sdrf file. If it is not able to obtain fastq paths, it will try to enter SRA Object file paths. If none are available, it will return the sdrf file leaving the file columns empty. If you find that the file columns are empty, you will need to update the file columns with file names and file paths manually. You could search for the file paths in the NCBI SRA database and/or ENA database. You will need to delete any unused empty columns.

**Download paths**

- All download paths should start with 'http://' or 'ftp://'. If you find an ftp path, it should start with the following: "ftp://ftp." The script accounts for this.

- Download paths should not be aws or google cloud paths i.e. file paths with 's3://' and 'gs://'. The script checks for this.

**Column names**

Below are examples of the file column names which should be included in the sdrf and thier order, given alternative file availability scenarios.

*Fastq paths were found*

*N.B. the script checks for a minimum of both read1 and read2 file paths.*

| Comment[read1 file] | Comment[FASTQ_URI]         | Comment[read2 file] | Comment[FASTQ_URI]         | Comment[index1 file] | Comment[FASTQ_URI]         |
|---------------------|----------------------------|---------------------|----------------------------|----------------------|----------------------------|
| example_R1.fastq.gz | [path]/example_R1.fastq.gz | example_R2.fastq.gz | [path]/example_R2.fastq.gz | example_I1.fastq.gz  | [path]/example_I1.fastq.gz |

,Or,

| Comment[read1 file] | Comment[FASTQ_URI]         | Comment[read2 file] | Comment[FASTQ_URI]         |
|---------------------|----------------------------|---------------------|----------------------------|
| example_R1.fastq.gz | [path]/example_R1.fastq.gz | example_R2.fastq.gz | [path]/example_R2.fastq.gz |

*Fastq paths were not found*

| Comment[read1 file] | Comment[read2 file]     | Comment[SRA_URI] |
|---------------------|-------------------------|------------------|
| SRR8448139_1.fastq  | SRR8448139_2.fastq      | SRR8448139       |

*SRA paths were not found*

* The script will leave the file columns empty. You will need to delete any unused empty columns.*

| Comment[read1 file] | Comment[FASTQ_URI] | Comment[read2 file] | Comment[FASTQ_URI] | Comment[SRA_URI] |
|---------------------|--------------------|---------------------|--------------------|------------------|
| PATHS NOT FOUND     | PATHS NOT FOUND    | PATHS NOT FOUND     | PATHS NOT FOUND    | PATHS NOT FOUND  |

#### Protocol Type format ####

- The Protocol Type columns should all have the same column name: Protocol REF
- All Protocol Type columns should be grouped together in the table, except, the sequencing Protocol REF column should be separate and follow technology type columns
- The name of the protocol REF ids in the idf file should match the Protocol IDs in the Protocol REF columns in the sdrf
- The order of the protocol REF ids in the idf file should match the order of the Protocol REF columns in the sdrf
- Each SCEA Protocol Type should have a single column: multiple protocol ids for the Protocol Type should be included in the same column

**Example**

*Project description*

Single-cell sequencing libraries were generated from 4 samples and sequenced. Samples 1 and 3 were collected from Human Lungs postmortem. Samples 2 and 4 were collected as biopsy samples from the kidneys of living humans during surgery. This resulted in 2 collection protocol ids: P-HCAD54-1 and P-HCAD54-2. All samples were dissociated by enzymatic dissociation: P-HCAD54-3. Samples 1 and 3 were subsequently enriched by cell size selection: P-HCAD54-4. Samples 2 and 4 were not subjected to an enrichment protocol. All samples were used for single cell library generation: P-HCAD54-5 and sequecing: P-HCAD54-6.

*idf Protocol metadata*

Protocol Type sample collection protocol  sample collection protocol  enrichment protocol enrichment protocol nucleic acid library construction protocol	nucleic acid sequencing protocol

Protocol Name P-HCAD54-1  P-HCAD54-2  P-HCAD54-3  P-HCAD54-4  P-HCAD54-5  P-HCAD54-6

*sdrf Protocol metadata*

 | Source Name    | Protocol REF   | Protocol REF  | Protocol REF  | Protocol REF |       | Protocol REF |
 |----------------|----------------|---------------|---------------|--------------|-------|--------------|
 | Sample1        | P-HCAD54-1     | P-HCAD54-3    | P-HCAD54-4    | P-HCAD54-5   |       | P-HCAD54-6   |
 | Sample2        | P-HCAD54-2     | P-HCAD54-3    |               | P-HCAD54-5   |       | P-HCAD54-6   |
 | Sample3        | P-HCAD54-1     | P-HCAD54-3    | P-HCAD54-4    | P-HCAD54-5   |       | P-HCAD54-6   |
 | Sample4        | P-HCAD54-2     | P-HCAD54-3    |               | P-HCAD54-5   |       | P-HCAD54-6   |

### Saving the files ###

- Make sure you save the idf file and sdrf file as a tab-delimited .txt file
- Make sure you remove any empty lines/spaces at the end of the file. They will cause validation errors.

## Validation

There are 2 validation steps for SCEA: a python validator and perl validator. In Silvie’s words: “the perl script checks the mage-tab format in general (plus some curation checks etc) and the the python script mainly checks for single-cell expression atlas specific fields and requirements”.

### Python Validator

#### Installing the tool ####

It is not possible to get this validation tool set-up globally in the /data/tools folder on EC2. It will need to be installed locally or in your home directory on EC2. If you follow the install instructions detailed here: https://pypi.org/project/atlas-metadata-validator/ you should be able to get it installed and running.


#### Running the tool ####

```
python atlas_validation.py path/to/test.idf.txt -sc -hca -v
```
*N.B. The tool will automatically detect the sdrf file given the idf filename prefix.*

- The experiment type should be set by specifying the optional argument: -sc
- The data file and URI checks may take a long time. Hence there is an option to skip these checks with -x
- Verbose logging can be activated with the optional argument: -v
- Invoke the special validation rules for HCA-imported experiments using the optional -hca argument

#### Error types ####

- An error message(s) will be printed, if an error is encountered
- An example of a successful validation looks like this:

![validation](https://github.com/ebi-ait/hca-ebi-wrangler-central/raw/master/assets/images/scea_screenshots/validation.png)

### Perl validator

#### Installing the tool ####

It is not possible to get this validation tool set-up globally in the /data/tools folder on EC2. It will need to be installed locally or in your home directory on EC2.mIf you follow the below install instructions you should be able to get it installed and running on EC2.

1.   Install Anaconda if you don’t have it already and the Anaconda directory to your path
2.   Configure conda by typing the following at the terminal:
     ```
     conda config --add channels defaults
     conda config --add channels bioconda
     conda config --add channels conda-forge
     ```
3.   Install the perl atlas module in a new environment: 
     ```
     conda create -n perl-atlas-test -c ebi-gene-expression-group perl-atlas-modules
     ```
4.   Activate the environment:
     ```
     conda activate perl-atlas-test
     ```
#### Running the tool ####

1. Copy the validate_magetab.pl perl script into your home or other directory where you will run the tool, it can be found on EC2 in the /data/tools/scea-perl-atlas-validator folder.

3. Ensure your idf file and sdrf file is in the same folder. The tool will automatically detect the sdrf file given the idf filename prefix.

5. Run the script:
     ```
     perl path-to/validate_magetab.pl -i <idf-file>
     ```
#### Error types ####

- An error message should appear next to specific error codes, e.g. SC-E03, SC-E04, SC-E02, SC-E05, GEN-E06. If there is no error message, please ask the scea team what this error means on the hca-to-scea slack channel, and record it in this SOP.
- The tool will return an error message saying that the HCA bundle UUID and HCA bundle version are not specified. You can ignore this error.
- An error message saying 'Additional attribute " " not found in SDRF' is likely causes by extra white space, tabs or empty lines in the input files.

## Where to send the files for review?

We do not need to send SCEA the raw data files. The file paths should be in the sdrf file. They will use the filepaths to obtain the raw data.

**HCA curators**

We now have a within-team secondary review process. Please move the dataset ticket to the new 'secondary review' column in the SCEA Zenhub Board and add a link to your idf and sdrf files. Please assign Ami as the secondary reviewer for now. This helps to highlight further areas for improvement of the hca2scea tool and the SOP.

**SCEA curators**

You should ask for access to the SCEA gitlab repo (https://gitlab.ebi.ac.uk/ebi-gene-expression/scxa-metadata), if you do not already have access. This is where we log in and upload the idf and sdrf files.

Once logged in, create a new branch from the master branch found here: https://gitlab.ebi.ac.uk/ebi-gene-expression/scxa-metadata/-/tree/master and name the new branch with the E-HCAD id you have assigned to the dataset. You should create a separate branch and folder for each E-HCAD dataset you upload.

Then, in the Gitlab HCAD directory in your new branch (https://gitlab.ebi.ac.uk/ebi-gene-expression/scxa-metadata/-/tree/master/HCAD) you will need to create a new folder named with the E-HCAD ID (e.g. E-HCAD-20) and upload the idf and sdrf files inside this new folder. Make sure you delete any .gitignore files that appear in the folder, if any.

Once done, you should create a merge request for the branch, and ensure an SCEA reviewer is tagged. It will by default assign an SCEA approver to the merge request, so you do not need to tag 1 of the SCEA curators yourself. For the merge request, adding a message like "Added new idf and sdrf files for accession E-HCAD-[number]" is fine.

You will recieve automated emails once you create the merge request. They will likely say that the pipeline has failed. The SCEA team will review the files and get back to us with comments, or if the pipeline passes the merge request will be approved. You will need to update the files in response to their feedback.

**Ticket management**

Once your dataset has been approved in Gitlab, you can close the ticket inside the Zenhub SCEA Review column.
