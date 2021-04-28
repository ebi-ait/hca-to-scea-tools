# HCA-TO-SCEA Tools

This repo contains various tools to help on the task of converting HCA spreadsheets to SCEA magetab files.

## hca2scea tool

### Installation

No need to install! It is installed on EC2. If you're a new team member and you need access to EC2 or permissions to run the tool, please speak with Amnon, our technical coordinator, or another HCA developer.

## Check points before curation

- Is this dataset valid in HCA ingest production? Ideally it will be, so that you can add the -id and -pd arguments (see below for arguments). If you want to curate before then, you can add a dummy value and modify the field in the output files later.

- Does this dataset consist of multiple species? If yes, you need to run the tool separately for each species and treat them as separate projects with separate E-HCAD-ids. There is a specific field in the idf file which can indicate related E-HCAD ids.

- Does this dataset consist of multiple technologies? If yes, you need to run the tool separately for each technology and treat them as separate projects with separate E-HCAD-ids. There is a specific field in the idf file which can indicate related E-HCAD ids. If the 10X version is mixed (v2 & v3), that can be kept as 1 project. 10X v1 is not a valid technology type, so needs to be removed from a project. There is a specific field in the idf file which can indicate related E-HCAD ids.

- Is the technology type valid for SCEA? Valid technology types are: 10X v2, 10X v3, Drop-seq, Smart-seq2, Smart-like, Seq-Well

- Is the full path to fastq files available for this dataset? If only bam files or SRA objects are available, you can continue to curate this dataset, using the fields: BAM URI and BAM file, or SRA URI and SRA file. However, this cannot currently be processed and should be uploaded to a shared folder, as opposed to SCEA's Gitlab. The SCEA team are working on a method to process these data types. For now, please see below section *Where to send the files for review?'* about uploading the MAGE-TAB to the appropriate location.

## Setting the environment on EC2

Go to the hca-to-scea-tools directory and activate the environment.
```
cd /data/tools/hca-to-scea-tools/hca2scea-backend
source venv/bin/activate
```

## Running the tool on EC2

```
python3 script.py -s [spreadsheet (xlsx)] -id [HCA project uuid] -c [curator initials] -tt [technology] -et [experiment type] -f [factor value] -pd [dataset publication date] -hd [hca last update date]
```
Example:
```
Python3 script.py -s /home/aday/GSE111976-endometrium_MC_SCEA.xlsx -id 379ed69e-be05-48bc-af5e-a7fc589709bf -c AD -tt 10Xv3_3 -et differential -f menstrual cycle day -pd 2021-06-29 -hd 2021-02-12
```

**How to assign a HCAD accession**

Please note that the script will automatically assign your dataset the next E-HCAD id in order using information about the unique E-HCAD accessions in the tracker sheet, unless you provide the -ac argument, which will override the default. Please ensure if you use this option that the E-HCAD id is unique and not already present in the tracker sheet.

**Arguments:**

| Argument   | Argument name            | Description                                                                                        | Required? |
|------------|--------------------------|----------------------------------------------------------------------------------------------------|-----------|
|-s          | HCA spreadsheet          | Path to HCA spreadsheet (.xlsx)                                                                    | yes       |
|-id         | HCA project uuid         | This is added to the 'secondary accessions' field in idf file                                      | yes       | 
|-c          | Curator initials         | HCA Curator initials.                                                                              | yes       |
|-ac         | ACCESSION_NUMBER         | Optional field to provide a SCEA accession, if not specified will be generated automatically       | no        |
|-tt         | Technology type          | Must be ['10Xv2_3','10Xv2_5','10Xv3_3','10Xv3_5','drop-seq','smart-seq','seq-well','smart-like']   | yes       |
|-et         | Experiment type          | Must be 1 of ['differential','baseline']                                                           | yes       |
|-f          | Factor value             | A list of user-defined factor values                                                               | yes       |
|-pd         | Dataset publication date | provide in YYYY-MM-DD E.g. from GEO                                                                | yes       |
|-hd         | HCA last update date     | provide in YYYY-MM-DD The last time the HCA project was updated in ingest  UI (production)         | yes       |
|--r         | Related E-HCAD-id        | If there is a related project, you should tner the related E-HCAD-id here                          | no        |
|-study      | study accession (SRPxxx) | The study accession will be used to find the paths to the fastq files for the given runs           | yes       |
|-name       | HCA name field           | Which HCA field to use for the biomaterial names columns. Must be ['']                             | no        |
|--facs.     | optional argument        | If FACS was used as a single cell isolation method, indicate this by adding the --facs argument.   | no        |

**Definitions:**

**Experiment type:** an experiment with samples which can be grouped or differentiatied by a factor value is classified as 'differential'. Baseline indicates an experiment with no clear grouping or factor value.
Example differential: normal and disease, multiple developmental stages
Example baseline: all primary samples from 1 organ type and same developmental stage and disease status.

**Factor value:** a factor value is a chosen experimental characteristic which can be used to group or differentiate samples. If there is no obvious factor value, 1 must be given. In this case, you can add 'individual', which indicates the unique donors. The SCEA team's validator tools will fail without this.
Example: disease developmental stage age

## Output files

The script will output an idf file and an sdrf file named with the same new E-HCAD-id. These files will be written into a new folder: `./hca2scea-backend/spreadsheets/<spreadsheet_name>/`.

Once you have copied the files to a location so you can manually curate them, please delete the folder from the above directory.

At this point you should enter the assigned E-HCAD id (e.g. E-HCAD-20) into the tracker sheet in all accession columns, as the script takes information from the tracker in order to assign the next E-HCAD id in order.

You should also note the E-HCAD id in the dataset ticket in the Dataset Wrangling Zenhub board and move the ticket to the SCEA conversion column.

The ticket should be moved to the SCEA review column only once the curated files have been handed over to the SCEA team, as described later on in this document.

## Further curation of the idf and sdrf files

Please see the example files folder to see how and where the below should appear.

Both files: The script accesses the tracker google sheet to determine the next E-HCAD-id (we curate them in increasing number order). You should therefore add the output E-HCAD-id in the tracker as soon as possible. If you will be running the script more than once, you will need to update the tracker in between these 2 runs. This is the only way we can attempt tp stay on top of this without an actual database. It is an imperfect solution given multiple users can run the tool at around the same time, but it should be ok for now. The E-HCAD-ids are not difficult to change in the idf file itself and both file names. You could also check that the E-HCAD-id your files are given is not already available in the tracker sheet, and is the roughly the next number in order, after running the tool, to be sure.

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
- You need to add new columns with the full download path to fastq files (FASTQ URI) and fastq file names. Please see examples.
- You need to add a factor value column as the last column in the sdrf file which matches the factor value(s) you gave as an argument and entered in the idf file.
- You will need to check that the number and name of the protocol REF ids in the idf file (e.g. P-HCADX-1,P-HCADX-2) matches correctly with the experiment rows in the sdrf files, based on the experimental design. The automatic conversion should be correct but this is a good check to do.
- Controlled vocabulary is applicable in certain sdrf fields: please see the shared documents from Silvie found here: [SCEA controlled vocabulary](https://drive.google.com/drive/folders/1GHaqpQsz4CY6_KkBTTXHJo69J4FXMNcw)
- For time unit ranges, please use ‘to’ instead of ‘-‘. For example: ‘20 to 60’ years.
- Make sure you save the sdrf file as a tab-delimited .txt file: beware of excel changing your time unit ranges to a date format and of empty rows/lines at the bottom of the file. Empty rows/lines will cause errors in validation.

## Validation

_There are 2 validation steps for SCEA: a python validator and perl validator. In Silvie’s words: “the perl script checks the mage-tab format in general (plus some curation checks etc) and the the python script mainly checks for single-cell expression atlas specific fields and requirements”._

### Python Validator

Please note: there is a ticket to get the validation tools installed on EC2. This should be available soon, as of 28/04/2021. For now, please install and run locally, following the instructions below.

A MAGE-TAB pre-validation module for running checks that guarantee the experiment can be processed for SCEA. You can clone the repository and run the script locally:

[Atlas metadata validator](https://github.com/ebi-gene-expression-group/atlas-metadata-validator)

To run, from the directory:

```
python atlas_validation.py path/to/test.idf.txt -sc -hca -v
```

*   The SDRF file is expected in the same directory as the IDF file. If this is not the case, the location of the SDRF and other data files can be specified with -d PATH_TO_DATA option.
*   The script guesses the experiment type (sequencing, microarray or single-cell) from the MAGE-TAB. If this was unsuccessful the experiment type can be set by specifying the respective argument -seq, -ma or -sc.
*   The data file and URI checks may take a long time. Hence there is an option to skip these checks with -x.
*   Verbose logging can be activated with -v.
*   Special validation rules for HCA-imported experiments can be invoked with -hca option. The validator will otherwise guess if the experiment is an HCA import based on the HCAD accession code in the ExpressionAtlasAccession field.

An example of a successful validation looks like this:

![validation](https://github.com/ebi-ait/hca-ebi-wrangler-central/raw/master/assets/images/scea_screenshots/validation.png)

### Perl validator

1.   Install Anaconda if you don’t have it already and the Anaconda directory to your path
1.   Configure conda by typing the following at the terminal:
     ```
     conda config --add channels defaults
     conda config --add channels bioconda
     conda config --add channels conda-forge
     ```
1.   Install the perl atlas module in a new environment: 
     ```
     conda create -n perl-atlas-test -c ebi-gene-expression-group perl-atlas-modules
     ```
1.   Activate the environment:
     ```
     conda activate perl-atlas-test
     ```
1.   Download the validate_magetab.pl_ _perl script from here: [https://drive.google.com/drive/folders/1Ja2NKtHkDh2YIvUhNa1mpivL-UjCsmbR](https://drive.google.com/drive/folders/1Ja2NKtHkDh2YIvUhNa1mpivL-UjCsmbR))
1.   Execute the script (with idf and sdrf files in the same directory)
     ```
     perl path-to/validate_magetab.pl -i <idf-file>
     ```
     (You can ignore ArrayExpress errors)

## Where to send the files for review?

We do not need to send them the fastq files. However, we do need to provide the full paths to the fastq files in the sdrf file. The latest version of the script should find and enter the file names into the sdrf file. However, it is best to check this in case the file paths were not found. If the script only finds paths to bam files or SRA objects, it is worth checking that the fastq file paths are really not openly available from NCBI or ENA to be sure (without a formal request to NCBI), though the script should account for this.

For datasets where the full paths to fastq files is entered in the sdrf file, you should first create a new branch from the master branch found here: https://gitlab.ebi.ac.uk/ebi-gene-expression/scxa-metadata/-/tree/master and name the new branch with the E-HCAD id you have assigned to the dataset. Then, in the Gitlab HCAD directory in this  new branch (https://gitlab.ebi.ac.uk/ebi-gene-expression/scxa-metadata/-/tree/master/HCAD) you will need to create a new folder named with the E-HCAD id (e.g. E-HCAD-20) and upload the idf and sdrf files inside this new folder. Once this is done, you should create a merge request for that branch, and ensure a reviewer is tagged (default). You should create a separate branch and folder for each E-HCAD dataset you upload. You will recieve automated emails once you create a merge request. They will probably say that the pipeline has failed. This is fine, you do not need to do anything. The SCEA team will review the uploaded files and make edits when they can to correct the datasets - it is from this point in their hands. However, you should look out for an email saying your dataset has been approved (most likely after some edits), so you know to close the ticket inside the Zenhub SCEA Review column so we keep on top of open tickets.

Next:
1. ensure you have updated the tracker sheet to include the new E-HCAD-ids, as the script uses this information to automatically generate the next E-HCAD id in order.
2. let the SCEA team know on slack that you have created a new branch (if you have more than 1 dataset to upload, it's best to notufy them once and refer to the group of E-HCAD ids).

For datasets where only the full paths to BAM files were available (these will be shown in the sdrf file), please upload the idf and sdrf files here: https://drive.google.com/drive/folders/1KNLOUZdDg7bYyCB19Jtvl2nt514K6Q1V Also create a new empty directory with this E-HCAD id in the Gitlab page so we know a dataset with this id exists and awaits upload.

For datasets where only the full paths to BAM files were available (these will be shown in the sdrf file), please upload the idf and sdrf files here: https://drive.google.com/drive/folders/1kIEJDZM1EIuCKTAM3nDh9Hvkysnjv8J0 Also create a new empty directory with this E-HCAD id in the Gitlab page so we know a dataset with this id exists and awaits upload.
