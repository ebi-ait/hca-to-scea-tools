# HCA-TO-SCEA Tools

This repo contains various tools to help on the task of converting HCA spreadsheets to SCEA magetab files.

## SCEA eligibility criteria

Before you start converting your dataset to SCEA format, you will need to decide if the dataset is eligible for SCEA.

### Project level eligibility criteria

- The dataset has been submitted to HCA DCP. You will need the project uuid and HCA DCP release date as input to the script.

### Technology type eligibility criteria

- The dataset consists of data generated by at least 1 type of single-cell RNA sequencing technology in the following list of eligible technology types: 10X v2, 10X v3, Drop-seq, Smart-seq2, Smart-like, Seq-Well
  
- The dataset consists of data generated from at most 1 single-cell RNA sequencing technology type. If the data is derived from more than 1 single-cell sequencing type, the dataset must be split into datasets separated by technology type and with separate E-HCAD-ids.

- Bulk RNA sequencing libraries are not eligible.

- If the dataset consists of 10X visium technology, it is eligible but please put the ticket in the stalled column until we have an SOP ready to for the curation of 10X visium data. The hca-to-scea tool does not currently support this technology type.

### Sample type eligibility criteria

- The dataset consists of data generated from at most 1 species. If the data is derived from more than 1 species, the dataset must be split into datasets separated by species and with separate E-HCAD-ids.

- If the dataset consists of organoid or iPSC sample types, it is eligible but please put the ticket in the stalled column until we have an SOP ready for this sample type. The hca-to-scea tool does not yet reliably support these sample types.

- Cell lines other than iPSC, hESC or organoid are not eligible e.g. 2D immortalised cell lines.

### Protocol type eligibility criteria

- Experiments involving cell-type enrichment using cell markers are eligible. However, the script does not currently support the addition list of the sample cell marker status. See below for guidance on how to manually add the cell marker status to the output sdrf file.

- Experiments involving treatment with a drug, stimulus or other treatment type are eligible. However, the script does not currently support the addition list of this protocol type or treatment status. See below for guidance on how to manually add a treatment protocol type and treatment status to the output idf file and sdrf file, respectively.

- Experiments involving a differentiation protocol are eligible. However, the script does not currently support the addition of this protocol type. See below for guidance on how to mnually add a differentiation protocol to the output idf file.

### Data availability criteria

- The full path to fastq files or SRA object files is available for the dataset run accessions. Datasets with only raw data in bam file format are not currently eligible.

## hca2scea tool

### Installation

The hca-to-scea tool is installed on EC2. If you're a new team member and you need access to EC2 or permissions to run the tool, please speak with Amnon, our technical coordinator, or another HCA developer.

### Copying your HCA spreadsheet to EC2

In order to use the hca-to-scea tool on EC2, you will need to copy your input HCA spreadsheet there, for example in your home folder. An example command to do this:

```
scp -i [OPENSSH PRIVATE KEY file path] [path to spreadsheet] [username]@tool.archive.data.humancellatlas.org:/home/[username]
```

### Setting the environment on EC2

Go to the hca-to-scea-tools directory and activate the environment.
```
cd /data/tools/hca-to-scea-tools/hca2scea-backend
source venv/bin/activate
```

### Running the tool on EC2

The easiest way might be to copy the example below, and replace the arguments as necessary whilst referring to this readme.

```
python3 hca2scea.py -s [spreadsheet (xlsx)] -id [hca project uuid] -study [study accession (SRPxxx)] -name {cs_name,cs_id,sp_name,sp_id,other} -ac [accession number] -c [curator initials] -tt [technology type] -et [experiment type] -f [factor values] -pd [dataset publication date] -hd [hca last update date] -r [related scea accession] --facs -o [output dir]
```

**Examples**

Required arguments only:
```
python3 hca2scea.py -s /home/aday/GSE111976-endometrium_MC_SCEA.xlsx -id 379ed69e-be05-48bc-af5e-a7fc589709bf -study SRP135922 -ac 50 -c AD -tt 10Xv3_3 -et differential -f menstrual cycle day -pd 2021-06-29 -hd 2021-02-12
```

Specify optional name argument:
```
python3 hca2scea.py -s /home/aday/GSE111976-endometrium_MC_SCEA.xlsx -id 379ed69e-be05-48bc-af5e-a7fc589709bf -study SRP135922 -name cs_name -ac 50 -c AD -tt 10Xv3_3 -et differential -f menstrual cycle day -pd 2021-06-29 -hd 2021-02-12
```

Specify optional related scea accession:
```
python3 hca2scea.py -s /home/aday/GSE111976-endometrium_MC_SCEA.xlsx -id 379ed69e-be05-48bc-af5e-a7fc589709bf -study SRP135922 -ac 50 -c AD -tt 10Xv3_3 -et differential -f menstrual cycle day -pd 2021-06-29 -hd 2021-02-12 -r 51
```

Specify that FACS was used:
```
python3 hca2scea.py -s /home/aday/GSE111976-endometrium_MC_SCEA.xlsx -id 379ed69e-be05-48bc-af5e-a7fc589709bf -study SRP135922 -ac 50 -c AD -tt 10Xv3_3 -et differential -f menstrual cycle day -pd 2021-06-29 -hd 2021-02-12 --facs
```

Specify optional output dir:
```
python3 hca2scea.py -s /home/aday/GSE111976-endometrium_MC_SCEA.xlsx -id 379ed69e-be05-48bc-af5e-a7fc589709bf -study SRP135922 -ac 50 -c AD -tt 10Xv3_3 -et differential -f menstrual cycle day -pd 2021-06-29 -hd 2021-02-12 -o my_output_dir
```

**How to choose an E-HCAD accession number**

Please check the [tracker sheet](https://docs.google.com/spreadsheets/d/1rm5NZQjE-9rZ2YmK_HwjW-LgvFTTLs7Q6MzHbhPftRE/edit#gid=0) for the next suitable E-HCAD accession number. Please ensure the E-HCAD id you choose is unique and not already present in the tracker sheet. It should be the next consecutive number after the maximum number in the sheet.
It is also a good idea to notify in hca-wrangler-metadata that you are doing some SCEA wrangling to ensure the E-HCAD-id does not get duplicated. The accession is a required argument for the script.

**Example**

Accessions E-HCAD1 to E-HCAD32 have already been assigned to datasets.
The next accession number would be 33.

**Arguments:**

| Argument   | Argument name            | Description                                                                                        | Required? |
|------------|--------------------------|----------------------------------------------------------------------------------------------------|-----------|
|-s          | HCA spreadsheet          | Path to HCA spreadsheet (.xlsx)                                                                    | yes       |
|-id         | HCA project uuid         | This is added to the 'secondary accessions' field in idf file                                      | yes       | 
|-c          | Curator initials         | HCA Curator initials. Space-separated list.                                                                             | yes       |
|-ac         | accession number         | Provide an SCEA accession number (integer).                                                        | yes       |
|-tt         | Technology type          | Must be ['10Xv2_3','10Xv2_5','10Xv3_3','10Xv3_5','drop-seq','smart-seq','seq-well','smart-like']   | yes       |
|-et         | Experiment type          | Must be 1 of ['differential','baseline']                                                           | yes       |
|-f          | Factor value             | A space-separated list of user-defined factor values e.g. age disease                              | yes       |
|-pd         | Dataset publication date | provide in YYYY-MM-DD E.g. from GEO                                                                | yes       |
|-hd         | HCA last update date     | provide in YYYY-MM-DD The last time the HCA project was updated in ingest  UI (production)         | yes       |
|-r          | Related E-HCAD-id        | If there is a related project, you should enter the related E-HCAD-id here e.g.['E-HCAD-39']       | no        |
|-study      | study accession (SRPxxx) | The study accession will be used to find the paths to the fastq files for the given runs           | yes       |
|-name       | HCA name field           | Which HCA field to use for the biomaterial names columns. Must be 1 of                             | no        |
|            |                          | ['cs_name, cs_id, sp_name, sp_id, other'] where cs indicates "cell suspension" and sp indicates    |           |
|            |                          |    "specimen from organism". Default is cs_name.                                                   |           |
|--facs      | optional argument        | If FACS was used as a single cell isolation method, indicate this by adding the --facs argument.   | no        |
|-o          | optional argument        | An output dir path can optionally be provided. If it does not exist, it will be created.           | no

**Definitions:**

**Experiment type:**

An experiment with samples which can be grouped or differentiatied by a factor value is classified as 'differential'. Baseline indicates an experiment with no clear grouping or factor value.

**Example differential:**

normal and disease, multiple developmental stages

**Example baseline:**

all primary samples from 1 organ type and same developmental stage and disease status.

**Factor value:**

A factor value is a chosen experimental characteristic which can be used to group or differentiate samples. **If there is no obvious factor value, 1 must be given. In this case, you can add 'individual', which indicates the unique donors.** The SCEA team's validator tools will fail without this.

Technology cannot be a factor value.

**Example:**

individual, disease, developmental stage, age

A list of example factor values that could be used has also been provided by the scea team here: https://docs.google.com/spreadsheets/d/1NQ5c7eqaFHnIC7e359ID5jtSawyOcnyv/edit#gid=1742687040

**Related E-HCAD-id:**

If the project has been split into two separate E-HCAD datasets, due to different technologies being used in the same project, or any other reason, then enter the E-HCAD-ID for the other dataset here.

**Example**

E-HCAD-34

## Output files

The script will output an idf file and an sdrf file named with the same new E-HCAD-id. These files will be written into a new folder: `./hca2scea-backend/script_spreadsheets/<spreadsheet_name>/`.

You will then need to copy them to your local desktop to further manually curate them. Please delete the folder from the above directory once you have done this. An example command to do this is below. It must be run from the terminal on your local desktop, not from inside EC2:

```
scp -i [OPENSSH PRIVATE KEY file path] [username]@tool.archive.data.humancellatlas.org:/home/tools/hca-to-scea-tools/hca2scea-backend/script_spreadsheets/[your output dir] [local folder path] 
```

Alternatively, see [here](https://ebi-ait.github.io/hca-ebi-wrangler-central/tools/handy_snippets.html#transfer-files-between-local-machine-and-ec2-scp-rsync) for tips on how to do this.

## Update tracker sheet with newly assigned E-HCAD ID

At this point you should enter the newly assigned E-HCAD id(s) (e.g. E-HCAD-33) into the [tracker sheet](https://docs.google.com/spreadsheets/d/1rm5NZQjE-9rZ2YmK_HwjW-LgvFTTLs7Q6MzHbhPftRE/edit#gid=0). Please enter in all relevent accession columns to make sure they are visible to other wranglers when they select the next E-HCAD accession number for their dataset.

Please also note the E-HCAD id in the dataset ticket in the HCA Dataset Wrangling Zenhub board.

Please also manage the SCEA curation status of your dataset using the SCEA wrangling Zenhub board.

## Further curation of the idf and sdrf files

Please see the example files folder to see how and where the below should appear.

idf file:
- Use a tab to separate every value you enter. Also, the spacing created by tabs is important, for example, tabs between author names or emails, including where the email is not known and shown as a blank.
- The Protocol Name is used in the sdrf file to detail which protocols are applied in which experiments. It is worth checking these are all correct in the sdrf after running the tool.
- The protocol Name should be ordered by number.
- The protocol Type and Description order must reflect the Name order https://github.com/ebi-gene-expression-group/atlas-fastq-provider
- The protocol types are: sample collection protocol, enrichment protocol, nucleic acid library construction protocol, nucleic acid sequencing protocol. These should be obvious except that the enrichment protocol indicates both an HCA dissociation protocol and an HCA enrichment protocol (and should be entered twice to reflect those 2). In terms of differentiation protocol, ipsc induction protocol or other, we should ask Anja or Nancy how they approach that.
- Each protocol description should be simplified and include less extensive details than the HCA standard. The SCEA team prefer the protocols have general and short descriptions which provide enough information to interpret the data.
- You need to add the chosen factor values given as an input argument in the idf file in both of these fields: Experimental Factor Name and Experimental Factor Type
- You should add at least the 'individual', 'sex' and 'age' fields if they are available, using the following field: Comment[EAAdditionalAttributes]
- Other 'Comment' fields that you think are useful to display in the SCEA browser can be chosen and added to the Comment[EAAdditionalAttributes]. However, they should not be Factor Values. All metadata will be displayed in a table in browser. However, these specific attributes will be displayed as a user hovers over individual cells in their multi-dimensional cell visualisation tool. Some examples are: immunophenotype, treatment, stimulus, if they are not Factor Values.
- You should add a related project E-HCAD-id if the project was split into separate E-HCAD-ids by adding this field: Comment[RelatedExperiment]

sdrf file:
- The format should be 1 RUN per row, with files (read1,read2,index1) in separate Comment columns.
- You need to add new columns with the full download path to fastq files and fastq file names. The column names should be "Comment[read1 file]" and "Comment[FASTQ_URI]" respectively and "Comment[read2 file]" and "Comment[FASTQ_URI]" respectively. You should also add "Comment[index1 file]" and "Comment[FASTQ_URI]" respectively if there is an index1 file available. A "Comment[FASTQ_URI]" column with the relevant file paths should always following a "Comment[[enter read index] file]" column. It is currently up to the wrangler to identify the names and full paths of the fastq files either in the NCBI SRA or ENA DB. The full download path should start with 'http://' or 'ftp://'. If you find an ftp path, it should start with the following: "ftp://ftp.". While I am in the process of automating getting the fastq file paths into the sdrf file, I am waiting to be on development until I can get this finished. Therefore, for now the "ftp://" prefix will need to be added to the paths manually or via a small script. If a path to the fastq files can not be found, the fastq file columns should be removed from the sdrf file. They should be replaced with Comment[SRA file] and Comment[SRA_URI] or Comment[BAM file] and Comment[BAM_URI] respectively. If the paths to an SRA object can be found then that is preferred over a path to the bam files as the scea team cannot currently process bam files.
- You need to add a factor value column as the last column in the sdrf file which matches the factor value(s) you gave as an argument and entered in the idf file.
- You will need to check that the number and name of the protocol REF ids in the idf file (e.g. P-HCADX-1,P-HCADX-2) matches correctly with the experiment rows in the sdrf files, based on the experimental design. The automatic conversion should be correct but this is a good check to do.
- Add a new Comment[technical replicate group] column if there are multiple runs per sample. This column should be added immediately following the Assay Name column. The column values should be either the Biosample IDs or given group ids e.g. group1,group2, etc.
- For time unit ranges, please use ‘to’ instead of ‘-‘. For example: ‘20 to 60’ years.
- Make sure you save the sdrf file as a tab-delimited .txt file: beware of excel changing your time unit ranges to a date format and of empty rows/lines at the bottom of the file. Empty rows/lines will cause errors in validation.

## Validation

There are 2 validation steps for SCEA: a python validator and perl validator. In Silvie’s words: “the perl script checks the mage-tab format in general (plus some curation checks etc) and the the python script mainly checks for single-cell expression atlas specific fields and requirements”.

### Python Validator

It is not possible to get this validation tool running globally for all users in the /data/tools folder on EC2. It is better to install it individually in your home directory or subdirectory. If you follow the install instructions detailed here: https://pypi.org/project/atlas-metadata-validator/ you should be able to get it installed and running.

To run the tool once installed, type this command, indicating the path to the idf file which you wish to validate. The corresponding sdrf file should be in the same folder. The tool will automatically detect the sdrf file given the idf filename prefix:

```
python atlas_validation.py path/to/test.idf.txt -sc -hca -v
```
*   The script guesses the experiment type (sequencing, microarray or single-cell) from the MAGE-TAB. If this was unsuccessful the experiment type can be set by specifying the respective argument -seq, -ma or -sc.
*   The data file and URI checks may take a long time. Hence there is an option to skip these checks with -x.
*   Verbose logging can be activated with -v.
*   Special validation rules for HCA-imported experiments can be invoked with -hca option. The validator will otherwise guess if the experiment is an HCA import based on the HCAD accession code in the ExpressionAtlasAccession field.

An example of a successful validation looks like this:

![validation](https://github.com/ebi-ait/hca-ebi-wrangler-central/raw/master/assets/images/scea_screenshots/validation.png)

### Perl validator

It is not possible to get this validation tool running globally for all users in the /data/tools folder on EC2. It is better to install it individually in your home directory or subdirectory. If you follow the below install instructions you should be able to get it installed and running on EC2.

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
5.   Copy the validate_magetab.pl perl script into your home or other directory where you will run the tool, it can be found on EC2 in the /data/tools/scea-perl-atlas-validator folder. The corresponding sdrf file should be in the same folder. The tool will automatically detect the sdrf file given the idf filename prefix.
6.   Execute the script (with idf and sdrf files in the same directory)
     ```
     perl path-to/validate_magetab.pl -i <idf-file>
     ```
     (You can ignore ArrayExpress errors)

## Where to send the files for review?

We do not need to send them the fastq files. However, we do need to provide the full paths to the fastq files in the sdrf file. The latest version of the script should find and enter the file names into the sdrf file. However, it is best to check this in case the file paths were not found. If the script only finds paths to bam files or SRA objects, it is worth checking that the fastq file paths are really not openly available from NCBI or ENA to be sure (without a formal request to NCBI), though the script should account for this.

For datasets where the full paths to fastq files is entered in the sdrf file, you should first create a new branch from the master branch found here: https://gitlab.ebi.ac.uk/ebi-gene-expression/scxa-metadata/-/tree/master and name the new branch with the E-HCAD id you have assigned to the dataset. Then, in the Gitlab HCAD directory in this  new branch (https://gitlab.ebi.ac.uk/ebi-gene-expression/scxa-metadata/-/tree/master/HCAD) you will need to create a new folder named with the E-HCAD id (e.g. E-HCAD-20) and upload the idf and sdrf files inside this new folder. Once this is done, you should create a merge request for that branch, and ensure a reviewer is tagged (default). You should create a separate branch and folder for each E-HCAD dataset you upload. You will recieve automated emails once you create a merge request. They will probably say that the pipeline has failed. This is fine, you do not need to do anything. The SCEA team will review the uploaded files and make edits when they can to correct the datasets - it is from this point in their hands. However, you should look out for an email saying your dataset has been approved (most likely after some edits), so you know to close the ticket inside the Zenhub SCEA Review column so we keep on top of open tickets.

Next:
Let the SCEA team know on slack that you have created a new branch (if you have more than 1 dataset to upload, it's best to notufy them once and refer to the group of E-HCAD ids).

For datasets where only the full paths to BAM files were available (these will be shown in the sdrf file), please upload the idf and sdrf files here: https://drive.google.com/drive/folders/1KNLOUZdDg7bYyCB19Jtvl2nt514K6Q1V Also create a new empty directory with this E-HCAD id in the Gitlab page so we know a dataset with this id exists and awaits upload.

For datasets where only the full paths to BAM files were available (these will be shown in the sdrf file), please upload the idf and sdrf files here: https://drive.google.com/drive/folders/1kIEJDZM1EIuCKTAM3nDh9Hvkysnjv8J0 Also create a new empty directory with this E-HCAD id in the Gitlab page so we know a dataset with this id exists and awaits upload.
