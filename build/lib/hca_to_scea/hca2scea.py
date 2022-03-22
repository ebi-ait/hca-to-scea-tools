import argparse
import json
import os
import sys
import pandas as pd
import copy
import zipfile

from hca_to_scea.helpers import multitab_excel_to_single_txt
from hca_to_scea.helpers import get_protocol_map
from hca_to_scea.helpers import fetch_fastq_path
from hca_to_scea.helpers import utils
from hca_to_scea.helpers import check_experimental_design
from hca_to_scea.helpers import split_dataset

pd.options.mode.chained_assignment = None

def rename_technology_type(technology_type, technology_dict):

    json_file = technology_dict[technology_type]

    return json_file

def get_person_roles(xlsx_dict):

    person_roles = utils.reformat_value(xlsx_dict, "project_contributors", "project.contributors.project_role.text")
    person_roles_submitter = utils.reformat_value(xlsx_dict, "project_contributors",
                                                  "project.contributors.corresponding_contributor")

    for (i, elem) in enumerate(person_roles_submitter):
        person_roles[i] = person_roles[i].lower()
        if elem == "yes":
            person_roles[i] = "submitter"
        elif elem == "no":
            if "curator" in person_roles[i]:
                person_roles[i] = "data curator"
            else:
                person_roles[i] = ""

    return person_roles

def get_author_list(xlsx_dict):

    authors = utils.reformat_value(xlsx_dict, "project_publications", "project.publications.authors")[0]
    author_list = authors.replace("||",", ")

    return author_list

def generate_idf_file(args, dataset_protocol_map, xlsx_dict, accession,
                      sdrf_file_name, related_scea_accessions):

    tab = '\t'
    person_roles = get_person_roles(xlsx_dict)
    #secondary_accessions = get_secondary_accessions(tracking_sheet, args) TBD from ingest.
    protocol_fields = get_protocol_map.get_idf_file_protocol_fields(dataset_protocol_map)
    author_list = get_author_list(xlsx_dict)

    related_scea_accessions = split_dataset.get_related_scea_accessions(accession, related_scea_accessions)

    if related_scea_accessions:

        idf_file_contents = f"""\

MAGE-TAB Version\t1.1
Investigation Title\t{utils.reformat_value(xlsx_dict, "project", "project.project_core.project_title")[0]}
Comment[Submitted Name]\t{utils.reformat_value(xlsx_dict, "project", "project.project_core.project_short_name")[0]}
Experiment Description\t{utils.reformat_value(xlsx_dict, "project", "project.project_core.project_description")[0]}
Public Release Date\t{args.public_release_date}
Person First Name\t{utils.get_tab_separated_list(xlsx_dict, "project_contributors", "project.contributors.name", lambda x: x.split(',')[0])}
Person Last Name\t{utils.get_tab_separated_list(xlsx_dict, "project_contributors", "project.contributors.name", lambda x: x.split(',')[2])}
Person Mid Initials\t{utils.get_tab_separated_list(xlsx_dict, "project_contributors", "project.contributors.name", lambda x: utils.get_first_letter(x.split(',')[1]))}
Person Email\t{utils.get_tab_separated_list(xlsx_dict, "project_contributors", "project.contributors.email")}
Person Affiliation\t{utils.get_tab_separated_list(xlsx_dict, "project_contributors", "project.contributors.institution")}
Person Address\t{utils.get_tab_separated_list(xlsx_dict, "project_contributors", "project.contributors.address")}
Person Roles\t{tab.join(person_roles)}
Protocol Type\t{tab.join([field[0] for field in protocol_fields])}
Protocol Name\t{tab.join([field[1] for field in protocol_fields])}
Protocol Description\t{tab.join([field[2] for field in protocol_fields])}
Protocol Hardware\t{tab.join([field[3] for field in protocol_fields])}
Term Source Name\tEFO\tArrayExpress
Term Source File\thttp://www.ebi.ac.uk/efo/efo.owl\thttp://www.ebi.ac.uk/arrayexpress/
Comment[AEExperimentType]\tRNA-seq of coding RNA from single cells
Experimental Factor Name\t{tab.join(args.experimental_factors)}
Experimental Factor Type\t{tab.join(args.experimental_factors)}
Comment[EAAdditionalAttributes]\t{''}
Comment[EACurator]\t{tab.join(args.curators)}
Comment[EAExpectedClusters]\t
Comment[ExpressionAtlasAccession]\t{accession}
Comment[RelatedExperiment]\t{tab.join(related_scea_accessions)}
Comment[HCALastUpdateDate]\t{args.hca_update_date}
Comment[SecondaryAccession]\t{args.project_uuid}
Comment[EAExperimentType]\t{args.experiment_type}
SDRF File\t{sdrf_file_name}

Investigation Title\t{utils.reformat_value(xlsx_dict, "project_publications", "project.publications.title")[0]}
Publication Author List\t{author_list}
PubMed ID\t{utils.reformat_value(xlsx_dict, "project_publications", "project.publications.doi")}
Publication DOI\t{utils.reformat_value(xlsx_dict, "project_publications", "project.publications.doi")[0]}
"""
    else:

        idf_file_contents = f"""\

MAGE-TAB Version\t1.1
Investigation Title\t{utils.reformat_value(xlsx_dict, "project", "project.project_core.project_title")[0]}
Comment[Submitted Name]\t{utils.reformat_value(xlsx_dict, "project", "project.project_core.project_short_name")[0]}
Experiment Description\t{utils.reformat_value(xlsx_dict, "project", "project.project_core.project_description")[0]}
Public Release Date\t{args.public_release_date}
Person First Name\t{utils.get_tab_separated_list(xlsx_dict, "project_contributors", "project.contributors.name", lambda x: x.split(',')[0])}
Person Last Name\t{utils.get_tab_separated_list(xlsx_dict, "project_contributors", "project.contributors.name", lambda x: x.split(',')[2])}
Person Mid Initials\t{utils.get_tab_separated_list(xlsx_dict, "project_contributors", "project.contributors.name", lambda x: utils.get_first_letter(x.split(',')[1]))}
Person Email\t{utils.get_tab_separated_list(xlsx_dict, "project_contributors", "project.contributors.email")}
Person Affiliation\t{utils.get_tab_separated_list(xlsx_dict, "project_contributors", "project.contributors.institution")}
Person Address\t{utils.get_tab_separated_list(xlsx_dict, "project_contributors", "project.contributors.address")}
Person Roles\t{tab.join(person_roles)}
Protocol Type\t{tab.join([field[0] for field in protocol_fields])}
Protocol Name\t{tab.join([field[1] for field in protocol_fields])}
Protocol Description\t{tab.join([field[2] for field in protocol_fields])}
Protocol Hardware\t{tab.join([field[3] for field in protocol_fields])}
Term Source Name\tEFO\tArrayExpress
Term Source File\thttp://www.ebi.ac.uk/efo/efo.owl\thttp://www.ebi.ac.uk/arrayexpress/
Comment[AEExperimentType]\tRNA-seq of coding RNA from single cells
Experimental Factor Name\t{tab.join(args.experimental_factors)}
Experimental Factor Type\t{tab.join(args.experimental_factors)}
Comment[EAAdditionalAttributes]
Comment[EACurator]\t{tab.join(args.curators)}
Comment[EAExpectedClusters]\t
Comment[ExpressionAtlasAccession]\t{accession}
Comment[HCALastUpdateDate]\t{args.hca_update_date}
Comment[SecondaryAccession]\t{args.project_uuid}
Comment[EAExperimentType]\t{args.experiment_type}
SDRF File\t{sdrf_file_name}

Investigation Title\t{utils.reformat_value(xlsx_dict, "project_publications", "project.publications.title")[0]}
Publication Author List\t{author_list}
PubMed ID\t{utils.reformat_value(xlsx_dict, "project_publications", "project.publications.pmid")}
Publication DOI\t{utils.reformat_value(xlsx_dict, "project_publications", "project.publications.doi")[0]}
"""

    return idf_file_contents

def reformat_age(age_list):

    updated_age_list = []

    for age in age_list:
        age = str(age)
        if ' - ' in age:
            age = age.replace('-', 'to')
        elif '-' in age and ' ' not in age:
            age = age.replace('-', ' to ')
        else:
            age = age

        updated_age_list.append(age)

    return updated_age_list


def get_sample_name_key(args, df):

    if args.name == 'cs_name':
        sample_name_key = 'cell_suspension.biomaterial_core.biomaterial_name'
    elif args.name == 'cs_id':
        sample_name_key = 'cell_suspension.biomaterial_core.biomaterial_id'
    elif args.name == 'sp_name':
        sample_name_key = 'specimen_from_organism.biomaterial_core.biomaterial_name'
    elif args.name == 'sp_id':
        sample_name_key = 'specimen_from_organism.biomaterial_core.biomaterial_id'

    return sample_name_key


def get_values_from_df(df, column):
    return df[column] if column in df.columns else ['']*df.shape[0]

def add_sequence_paths(sdrf, args):

    run_accessions = list(sdrf['Comment[ENA_RUN]'])

    try:
        sra_paths = fetch_fastq_path.get_sra_path_from_ena(args.study, run_accessions)
    except:
        sra_paths = fetch_fastq_path.get_sra_path_from_sra(args.study, run_accessions)
        if not sra_paths:
            try:
                sra_paths = fetch_fastq_path.get_sra_path_from_sra(run_accessions)
            except:
                sra_paths = fetch_fastq_path.get_sra_path_from_ena(args.study, run_accessions)

    if sra_paths:
        read1_names = []
        read2_names = []
        sra_names = []
        for key in sra_paths.keys():
            read1_names.append(key + "_1.fastq.gz")
            read2_names.append(key + "_2.fastq.gz")
            sra_names.append(sra_paths[key]['files'][0])
        sdrf['Comment[read1 file]'] = read1_names
        sdrf['Comment[read2 file]'] = read2_names
        sdrf['Comment[SRA_URI]'] = sra_names
    else:
        print("Could not find paths to SRA objects.")
        sdrf['Comment[SRA_URI]'] = 'PATH NOT FOUND'
        sdrf['Comment[read1 file]'] = 'PATH NOT FOUND'
        sdrf['Comment[read2 file]'] = 'PATH NOT FOUND'

    return sdrf


def get_new_protocol_column_names(sdrf, counter):

    new_column_names = []
    for col in sdrf.columns:
        column_name = "Protocol REF" + "_" + str(counter)
        counter += 1
        new_column_names.append(column_name)

    return new_column_names, counter

def order_protocols(protocols_sdrf_before_sequencing):
    collection_protocol_cols = []
    dissociation_protocol_cols = []
    enrichment_protocol_cols = []
    differentiation_protocol_cols = []
    library_preparation_protocol_cols = []
    for col in list(protocols_sdrf_before_sequencing.columns):
        if col.split(".protocol_core.protocol_id")[0] == "collection_protocol":
            collection_protocol_cols.append(col)
        if col.split(".protocol_core.protocol_id")[0] == "dissociation_protocol":
            dissociation_protocol_cols.append(col)
        if col.split(".protocol_core.protocol_id")[0] == "enrichment_protocol":
            enrichment_protocol_cols.append(col)
        if col.split(".protocol_core.protocol_id")[0] == "differentiation_protocol":
            differentiation_protocol_cols.append(col)
        if col.split(".protocol_core.protocol_id")[0] == "library_preparation_protocol":
            library_preparation_protocol_cols.append(col)
    new_columns = [sorted(collection_protocol_cols),sorted(dissociation_protocol_cols),sorted(enrichment_protocol_cols),sorted(differentiation_protocol_cols),sorted(library_preparation_protocol_cols)]
    new_columns = [item for sublist in new_columns for item in sublist]
    protocols_sdrf_before_sequencing = protocols_sdrf_before_sequencing[new_columns]
    return protocols_sdrf_before_sequencing

def add_protocol_columns(df, dataset_protocol_map):

    def convert_term(term, name):
        return get_protocol_map.map_proto_to_id(term, dataset_protocol_map)

    def convert_row(row):
        return row.apply(lambda x: convert_term(x, row.name))

    protocols_list_before_sequencing = ['collection_protocol', 'dissociation_protocol', 'enrichment_protocol', 'differentiation_protocol', 'library_preparation_protocol']

    protocols_sdrf_before_sequencing = df[[col for (proto_type, cols) in get_protocol_map.map_of_hca_protocol_type_id_keys.items() if proto_type in
                 protocols_list_before_sequencing for col in cols]]

    protocols_sdrf_before_sequencing.fillna("", inplace=True)
    pd.set_option('display.max_columns', None)

    protocols_sdrf_before_sequencing = protocols_sdrf_before_sequencing.apply(convert_row)
    pd.set_option('display.max_columns', None)

    protocols_sdrf_before_sequencing = order_protocols(protocols_sdrf_before_sequencing)

    counter = 1
    new_column_names, counter = get_new_protocol_column_names(protocols_sdrf_before_sequencing, counter)
    protocols_sdrf_before_sequencing.columns = new_column_names

    protocols_sdrf_before_sequencing.fillna(value='', inplace=True)

    protocols_list_from_sequencing = ['sequencing_protocol']
    protocols_sdrf_from_sequencing = df[[col for (proto_type, cols) in get_protocol_map.map_of_hca_protocol_type_id_keys.items() if proto_type in protocols_list_from_sequencing for col in cols]]
    protocols_sdrf_from_sequencing = protocols_sdrf_from_sequencing.apply(convert_row)
    new_column_names, counter = get_new_protocol_column_names(protocols_sdrf_from_sequencing, counter)
    protocols_sdrf_from_sequencing.columns = new_column_names

    return protocols_sdrf_before_sequencing, protocols_sdrf_from_sequencing


def add_scea_specimen_columns(args, df, experimental_design):

    if experimental_design == "standard":

        '''Open dictionary of mapped hca2scea key:pairs for specimen metadata.'''
        with open(f"json_files/sdrf_map.json") as sdrf_map_file:
            sdrf_map = json.load(sdrf_map_file)

    else:

        if experimental_design == "cell_line_only":
            '''Open dictionary of mapped hca2scea key:pairs for specimen metadata.'''
            with open(f"json_files/sdrf_map_cell_line.json") as sdrf_map_file:
                sdrf_map = json.load(sdrf_map_file)

        elif experimental_design == "organoid":
            '''Open dictionary of mapped hca2scea key:pairs for specimen metadata.'''
            with open(f"json_files/sdrf_map_cell_line_organoid.json") as sdrf_map_file:
                sdrf_map = json.load(sdrf_map_file)

        else:
            '''Open dictionary of mapped hca2scea key:pairs for specimen metadata.'''
            with open(f"json_files/sdrf_map_organoid.json") as sdrf_map_file:
                sdrf_map = json.load(sdrf_map_file)

    '''Get user-specified HCA sample names key.'''
    sample_name_key = get_sample_name_key(args, df)

    '''Update dictionary of mapped hca2scea key:pairs with sample name key.'''
    sdrf_map.update({
        'Source Name': sample_name_key,
        'Assay Name': sample_name_key,
        'Scan Name': sample_name_key,
        'Extract Name': sample_name_key,
        'Comment[BioSD_SAMPLE]': 'cell_suspension.biomaterial_core.biosamples_accession',
        'Comment[ENA_EXPERIMENT]': 'cell_suspension.insdc_experiment.insdc_experiment_accession',
        'Comment[ENA_RUN]': 'sequence_file.insdc_run_accessions',
        'Comment[technical replicate group]': 'cell_suspension.biomaterial_core.biosamples_accession'
        })

    '''Extract the HCA metadata values using the HCA keys in sdrf_map.'''
    sdrf = pd.DataFrame({k: get_values_from_df(df, v) for k, v in sdrf_map.items()})
    sdrf = sdrf.fillna('')

    '''Reformat the age values so they are excel-friendly.'''
    sdrf['Characteristics[age]'] = reformat_age(list(sdrf['Characteristics[age]']))

    '''Reformat living status to align with SCEA controlled vocabulary.'''
    sdrf['Characteristics[organism status]'] = sdrf['Characteristics[organism status]'].apply(lambda x: 'alive' if x.lower() in ['yes', 'y'] else 'dead')

    '''Add Material Type using SCEA controlled vocabulary.'''
    sdrf['Material Type_1'] = 'cell'

    return sdrf

def generate_sdrf_file(args, df, xlsx_dict, dataset_protocol_map, experimental_design, technology_dict):

    '''Generate a dataframe with SCEA specimen metadata.'''
    sdrf_1 = add_scea_specimen_columns(args, df, experimental_design)

    '''Get technology-specific SCEA metadata and add to sdrf_1 dataframe.'''
    technology_type = list(xlsx_dict["library_preparation_protocol"]["library_preparation_protocol.library_construction_method.ontology_label"])[0]
    technology_type = rename_technology_type(technology_type,technology_dict)
    try:
        with open(f"json_files/{technology_type}.json") as technology_json_file:
            technology_type_dict = json.load(technology_json_file)
    except:
        print("Technology type {} is not yet supported. Please ask Ami to add it to the technology type map.".format(technology_type))
        sys.exit()
    for key in technology_type_dict.keys():
        sdrf_1[key] = technology_type_dict[key]

    '''Edit single cell isolation method if the user-specified that FACS was used.'''
    if args.facs is True:
        sdrf_1['Comment[single_cell_isolation]'] = 'FACS'*sdrf_1.shape[0]
    # To do: add 'Comment[single_cell_isolation]' == Fluidigm C1 for Fluidigm C1 experiments.

    '''To Do. Get immunophenotype and treatment/stimulus information, if there is any.'''
    #"Characteristics[immunophenotype]":"enrichment_protocol.markers"
    sdrf_1['Characteristics[immunophenotype]'] = '' * sdrf_1.shape[0]
    #"Characteristics[stimulus]":"cell_suspension.growth_conditions.drug_treatment","differentiation_protocol.small_molecules",
    sdrf_1['Characteristics[stimulus]'] = '' * sdrf_1.shape[0]

    '''Get the SRA object file names and file paths from SRA or ENA (try both).'''
    sdrf_2 = add_sequence_paths(sdrf_1, args)

    '''Check all required column names are present and reorder columns by SCEA defined order.'''

    with open(f"json_files/expected_columns.json", "r") as expected_columns_file:
        expected_columns_dict = json.load(expected_columns_file)

    if experimental_design == 'standard':
        expected_columns_ordered = expected_columns_dict['standard']
    elif experimental_design == 'organoid_only':
        expected_columns_ordered = expected_columns_dict['organoid_only']
    else:
        expected_columns_ordered = expected_columns_dict['cell_line']

    column_check = [col for col in expected_columns_ordered if col not in sdrf_2.columns]
    if column_check:
        print("Error: one or more expected columns is missing from sdrf.")
        print(column_check)
        sys.exit()
    else:
        sdrf_3 = sdrf_2[expected_columns_ordered]

    '''Add protocol columns with protocol metadata in the pre-defined SCEA column order.'''
    protocols_sdrf_before_sequencing, protocols_sdrf_from_sequencing = add_protocol_columns(df, dataset_protocol_map)

    idx = 18
    for col in protocols_sdrf_before_sequencing.columns:
        sdrf_3.insert(idx, col, list(protocols_sdrf_before_sequencing[col]))
        idx += 1

    idx = list(sdrf_3.columns).index('Comment[LIBRARY_SELECTION]') + 1
    for col in protocols_sdrf_from_sequencing.columns:
        sdrf_3.insert(idx, col, list(protocols_sdrf_from_sequencing[col]))
        idx += 1

    '''Fix Material Type and Protocol REF column names to SCEA standard columns.'''
    for col_name in sdrf_3.columns:
        if 'Protocol REF' in str(col_name):
            sdrf_3 = sdrf_3.rename(columns={col_name: "Protocol REF"})
        elif 'Material Type' in str(col_name):
            sdrf_3 = sdrf_3.rename(columns={col_name: "Material Type"})

    '''Remove empty columns if columns are optional.'''
    with open(f"json_files/optional_columns.json", "r") as optional_columns_file:
        optional_columns_dict = json.load(optional_columns_file)

    if experimental_design == 'standard':
        optional_columns = optional_columns_dict['standard']
    else:
        optional_columns = optional_columns_dict['cell_line']

    for column_name in optional_columns:
        if set(list(sdrf_3[column_name])) == {''}:
            sdrf_3 = sdrf_3.drop([column_name], axis=1)

    return sdrf_3

def create_magetab(xlsx_dict, dataset_protocol_map, df, args, experimental_design, accession_number, related_scea_accessions, technology_dict):

    accession = f"E-HCAD-{accession_number}"

    idf_file_name = f"{accession}.idf.txt"
    sdrf_file_name = f"{accession}.sdrf.txt"

    idf_file_contents = generate_idf_file(args, dataset_protocol_map, xlsx_dict, accession,
                                          sdrf_file_name, related_scea_accessions)

    sdrf_file_contents = generate_sdrf_file(args, df, xlsx_dict, dataset_protocol_map, experimental_design,
                                            technology_dict)

    return idf_file_contents, sdrf_file_contents, idf_file_name, sdrf_file_name

def main():
    parser = argparse.ArgumentParser(description="run hca -> scea tool")
    parser.add_argument(
        "-s",
        "--spreadsheet",
        type=str,
        required=True,
        help="Please provide a path to the HCA project spreadsheet."
    )
    parser.add_argument(
        "-id",
        "--project_uuid",
        type=str,
        required=True,
        help="Please provide an HCA ingest project submission id."
    )
    parser.add_argument(
        "-study",
        type=str,
        required=True,
        help="Please provide the SRA or ENA study accession."
    )
    parser.add_argument(
        "-name",
        type=str,
        required=False,
        default = 'cs_id',
        choices = ['cs_name','cs_id','sp_name','sp_id','other'],
        help="Please indicate which field to use as the sample name. cs=cell suspension, sp = specimen."
    )
    parser.add_argument(
        "-ac",
        "--accession_number",
        type=int,
        required=True,
        help="Provide an E-HCAD accession number. Please find the next suitable accession number by checking the google tracker sheet."
    )
    parser.add_argument(
        "-c",
        "--curators",
        nargs='+',
        required=True,
        help="space separated names of curators"
    )
    parser.add_argument(
        "-et",
        "--experiment_type",
        type=str,
        required=True,
        choices=['baseline','differential'],
        help="Please indicate whether this is a baseline or differential experimental design"
    )
    parser.add_argument(
        "-facs",
        action="store_true",
        required=False,
        help="Please specify if FACS was used to isolate single cells."
    )
    parser.add_argument(
        "-f",
        "--experimental_factors",
        nargs='+',
        required=True,
        help="space separated list of experimental factors"
    )
    parser.add_argument(
        "-pd",
        "--public_release_date",
        type=str,
        required=True,
        help="Please enter the public release date in this format: YYYY-MM-DD"
    )
    parser.add_argument(
        "-hd",
        "--hca_update_date",
        type=str,
        required=True,
        help="Please enter the last time the HCA prohect submission was updated in this format: YYYY-MM-DD"
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        required=False,
        help="Provide full path to preferred output dir"
    )
    parser.add_argument(
        "-zip",
        "--zip_format",
        action="store_true",
        required=False,
        help="Please indicate whether you would like the script to output all"
             "txt files separately or together in 1 zip file."
    )

    args = parser.parse_args()
    if not args.output_dir:
        work_dir = f"script_spreadsheets/{os.path.splitext(os.path.basename(args.spreadsheet))[0]}"
    else:
        work_dir = args.output_dir

    if args.zip_format:
        zip_file = zipfile.ZipFile('hca-to-scea.zip', 'w')
    else:
        zip_file = None

    '''Merge the multitab spreadsheet into a single dataframe, while preserving the relationships
    between HCA biomaterials and protocols.
    '''
    xlsx_dict = multitab_excel_to_single_txt.multitab_excel_to_dict(work_dir, args.spreadsheet)

    '''Remove unused protocol tabs and corresponding protocol id column.'''
    xlsx_dict_tmp2 = multitab_excel_to_single_txt.remove_unused_protocols(xlsx_dict)

    '''Check whether multiple library preparation protocol technology types or 10X versions were
    used. If so, split xlsx_dict into a list of dicts separated by the technology type. Then,
    create idf and sdrf files for each of the dicts.'''

    technology_dict = {
        "Fluidigm C1-based library preparation": "smart-like",
        "10X 3' v1": "10Xv1_3",
        "10X 5' v1": "10Xv1_5",
        "10X 3' v2": "10Xv2_3",
        "10X 5' v2": "10Xv2_5",
        "10X 3' v3": "10Xv3_3",
        "10X 3' v1 sequencing": "10Xv1_3",
        "10X 5' v1 sequencing": "10Xv1_5",
        "10X 3' v2 sequencing": "10Xv2_3",
        "10X 5' v2 sequencing": "10Xv2_5",
        "10x 3' v3 sequencing": "10Xv3_3",
        "Drop-seq": "drop-seq",
        "inDrop": "drop-seq",
        "Smart-like": "smart-like",
        "Smart-seq2": "smart-seq",
        "Smart-seq": "smart-seq"
    }

    list_xlsx_dict = split_dataset.split_metadata_by_technology(xlsx_dict_tmp2,technology_dict)

    if len(list_xlsx_dict) > 1:
        accession_number_idx = [i for i in range(0,len(list_xlsx_dict))]
        accession_number_list = [int(args.accession_number) + i for i in accession_number_idx]

    else:
        accession_number_idx = [0]
        accession_number_list = [args.accession_number]

    for i in range(0,len(list_xlsx_dict)):

        xlsx_dict = list_xlsx_dict[i]
        accession_number = accession_number_list[i]

        related_scea_accessions_idx = copy.deepcopy(accession_number_idx)
        related_scea_accessions_idx.remove(i)
        related_scea_accessions = [accession_number_list[i] for i in related_scea_accessions_idx]

        '''Run checks to see whether the experimental design is compatibile and save the experimental
        design type in a variable for later.'''

        ''' Get the experimental design '''
        experimental_design = check_experimental_design.get_experimental_design(xlsx_dict)

        ''' Check if samples are pooled '''
        pooled_samples = check_experimental_design.check_for_pooled_samples(xlsx_dict)
        if pooled_samples:
            print("The hca-to-scea tool does not support pooled donors or pooled samples."
                "The dataset should be curated manually.")
            sys.exit()

        '''The merged df consists of a row per read index (read1, read2, index1). To conform to
        SCEA MAGE-TAB format, the rows should be merged so that there is 1 row per unique run accession.
        '''
        merged_df = multitab_excel_to_single_txt.merge_dataframes(xlsx_dict,experimental_design)
        merged_df_unique_runs = merged_df.drop_duplicates(subset=['sequence_file.insdc_run_accessions'])
        clean_merged_df = multitab_excel_to_single_txt.clean_df(merged_df_unique_runs)

        '''Extract the list of unique protocol ids from protocol types which can have more than one instance and
        creates extra columns in the df for each of the ids.'''
        df = multitab_excel_to_single_txt.create_new_protocol_columns(clean_merged_df, xlsx_dict, experimental_design)

        '''Create a map between the HCA protocol id and a new assigned SCEA protocol id. Use it to store the
        key protocol metadata that will be added to the SCEA sdrf file.'''
        dataset_protocol_map = get_protocol_map.prepare_protocol_map(xlsx_dict, df, args)

        '''Refactoring of the below TBD.'''
        idf_file_contents, sdrf_file_contents, idf_file_name, sdrf_file_name = create_magetab(xlsx_dict, dataset_protocol_map, df, args, experimental_design, accession_number,related_scea_accessions,technology_dict)

        if not args.zip_format:
            utils.save_files(work_dir, idf_file_name, sdrf_file_name, idf_file_contents, sdrf_file_contents)
        else:
            utils.save_files_zip(zip_file, work_dir, idf_file_contents, sdrf_file_contents, idf_file_name,
                                 sdrf_file_name)

    if zip_file:
        zip_file.close()

if __name__ == '__main__':
    main()
