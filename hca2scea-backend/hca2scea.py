import argparse
import json
import os
import pandas as pd

from helpers import multitab_excel_to_single_txt
from helpers import get_protocol_map
from helpers import fetch_fastq_path
from helpers import utils


def get_secondary_accessions(tracking_sheet, args):

    accessions = utils.get_accessions_for_project(tracking_sheet, identifier=args.project_uuid)
    if accessions:
        accessions_uniq = utils.get_unique_accessions([accessions])
        [accessions_uniq.remove(accession) for accession in accessions_uniq if 'HCAD' in accession.upper()]
        if accessions_uniq:
            secondary_accessions = accessions_uniq
        else:
            secondary_accessions = []
    else:
        secondary_accessions = []

    return secondary_accessions


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


def generate_idf_file(work_dir, args, tracking_sheet, dataset_protocol_map, xlsx_dict, accession, idf_file_name,
                      sdrf_file_name):

    tab = '\t'
    person_roles = get_person_roles(xlsx_dict)
    secondary_accessions = get_secondary_accessions(tracking_sheet, args)
    protocol_fields = get_protocol_map.get_idf_file_protocol_fields(dataset_protocol_map)

    if args.related_scea_accession:

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
Comment[RelatedExperiment]\t{args.related_scea_accession}
Comment[HCALastUpdateDate]\t{args.hca_update_date}
Comment[SecondaryAccession]\t{args.project_uuid}\t{tab.join(secondary_accessions or [])}
Comment[EAExperimentType]\t{args.experiment_type}
SDRF File\t{sdrf_file_name}
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
Comment[SecondaryAccession]\t{args.project_uuid}\t{tab.join(secondary_accessions or [])}
Comment[EAExperimentType]\t{args.experiment_type}
SDRF File\t{sdrf_file_name}
"""

    print(f"saving {work_dir}/{idf_file_name}")
    with open(f"{work_dir}/{idf_file_name}", "w") as idf_file:
        idf_file.write(idf_file_contents)


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
    return df[column] if column in df.columns else df['UNDEFINED_FIELD']


def add_sequence_paths(sdrf, args):

    run_accessions = list(sdrf['Comment[ENA_RUN]'])

    paths_fastq = fetch_fastq_path.get_fastq_path_from_ena(args.study, run_accessions)
    if paths_fastq:
        paths = fetch_fastq_path.sort_fastq(paths_fastq)
    else:
        print("Paths to fastq files can not be found in ENA. Searching for paths to SRA object files in SRA.")
        paths_sra = fetch_fastq_path.get_fastq_path_from_sra(sdrf)
        if paths_sra:
            paths = fetch_fastq_path.sort_sra(paths_sra)
        if not paths_sra:
            paths = None

    try:
        sdrf = fetch_fastq_path.filter_paths(sdrf, paths)
    except:
        sdrf['Comment[SRA_URI]'] = 'PATH NOT FOUND'
        sdrf['Comment[read1 file]'] = 'PATH NOT FOUND'
        sdrf['Comment[read2 file]'] = 'PATH NOT FOUND'
        sdrf['Comment[index1 file]'] = ''
        sdrf['Comment[read1 FASTQ_URI]'] = 'PATH NOT FOUND'
        sdrf['Comment[read2 FASTQ_URI]'] = 'PATH NOT FOUND'
        sdrf['Comment[index1 FASTQ_URI]'] = ''
        print("Could not obtain fastq file paths or SRA file paths. Please record a ticket with the study ID and let"
                "Ami know. For now you will need to enter the file paths into the sdrf file manually.")

    return sdrf


def get_new_protocol_column_names(sdrf, counter):

    new_column_names = []
    for col in sdrf.columns:
        column_name = "Protocol REF" + "_" + str(counter)
        counter += 1
        new_column_names.append(column_name)

    return new_column_names, counter


def add_protocol_columns(df, dataset_protocol_map):

    def convert_term(term, name):
        return get_protocol_map.map_proto_to_id(term, dataset_protocol_map)

    def convert_row(row):
        return row.apply(lambda x: convert_term(x, row.name))

    protocols_list_before_sequencing = ['collection_protocol', 'dissociation_protocol', 'enrichment_protocol', 'library_preparation_protocol']

    protocols_sdrf_before_sequencing = df[[col for (proto_type, cols) in get_protocol_map.map_of_hca_protocol_type_id_keys.items() if proto_type in
                 protocols_list_before_sequencing for col in cols]]

    protocols_sdrf_before_sequencing = protocols_sdrf_before_sequencing.apply(convert_row)

    protocols_sdrf_before_sequencing_list = []

    for (_, row) in protocols_sdrf_before_sequencing.iterrows():
        short_row = list(set([x for x in row.tolist() if x != '']))
        short_row.sort()
        protocols_sdrf_before_sequencing_list.append(short_row)

    protocols_sdrf_before_sequencing = pd.DataFrame.from_records(protocols_sdrf_before_sequencing_list)

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


def add_scea_specimen_columns(args, df):

    '''Open dictionary of mapped hca2scea key:pairs for specimen metadata.'''
    with open(f"json_files/sdrf_map.json") as sdrf_map_file:
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


def generate_sdrf_file(work_dir, args, df, dataset_protocol_map, sdrf_file_name):

    '''Generate a dataframe with SCEA specimen metadata.'''
    sdrf_1 = add_scea_specimen_columns(args, df)

    '''Get technology-specific SCEA metadata and add to sdrf_1 dataframe.'''
    with open(f"json_files/{args.technology_type}.json") as technology_json_file:
        technology_dict = json.load(technology_json_file)
    for key in technology_dict.keys():
        sdrf_1[key] = technology_dict[key]

    '''Edit single cell isolation method if the user-specified that FACS was used.'''
    if args.facs is True:
        sdrf_1['Comment[single_cell_isolation]'] = 'FACS'*sdrf_1.shape[0]

    '''To Do. Get immunophenotype and treatment/stimulus information, if there is any.'''
    #"Characteristics[immunophenotype]":"enrichment_protocol.markers"
    sdrf_1['Characteristics[immunophenotype]'] = '' * sdrf_1.shape[0]
    #"Characteristics[stimulus]":"cell_suspension.growth_conditions.drug_treatment","differentiation_protocol.small_molecules",
    sdrf_1['Characteristics[stimulus]'] = '' * sdrf_1.shape[0]

    '''Get the fastq file names and file paths from ENA or alternatively, if not available, get the the SRA
    Object file names and file paths from the SRA database.'''
    sdrf_2 = add_sequence_paths(sdrf_1, args)

    '''Check all expected column names are present and reorder columns by SCEA defined order.'''
    expected_columns_ordered = [
    'Source Name',
    'Comment[BioSD_SAMPLE]',
    'Characteristics[organism]',
    'Characteristics[individual]',
    'Characteristics[sex]',
    'Characteristics[age]',
    'Unit[time unit]',
    'Characteristics[developmental stage]',
    'Characteristics[organism part]',
    'Characteristics[sampling site]',
    'Characteristics[cell type]',
    'Characteristics[immunophenotype]',
    'Characteristics[stimulus]',
    'Characteristics[disease]',
    'Characteristics[organism status]',
    'Characteristics[cause of death]',
    'Description',
    'Material Type_1',
    'Extract Name',
    'Material Type_2',
    'Comment[library construction]',
    'Comment[single cell isolation]',
    'Comment[input molecule]',
    'Comment[primer]',
    'Comment[end bias]',
    'Comment[umi barcode read]',
    'Comment[umi barcode offset]',
    'Comment[umi barcode size]',
    'Comment[cell barcode read]',
    'Comment[cell barcode offset]',
    'Comment[cell barcode size]',
    'Comment[sample barcode read]',
    'Comment[sample barcode offset]',
    'Comment[sample barcode size]',
    'Comment[cDNA read]',
    'Comment[cDNA read offset]',
    'Comment[LIBRARY_STRAND]',
    'Comment[LIBRARY_LAYOUT]',
    'Comment[LIBRARY_SOURCE]',
    'Comment[LIBRARY_STRATEGY]',
    'Comment[LIBRARY_SELECTION]',
    'Assay Name',
    'Technology Type',
    'Scan Name',
    'Comment[ENA_EXPERIMENT]',
    'Comment[technical replicate group]',
    'Comment[ENA_RUN]',
    'Comment[read1 file]',
    'Comment[read1 FASTQ_URI]',
    'Comment[read2 file]',
    'Comment[read2 FASTQ_URI]',
    'Comment[index1 file]',
    'Comment[index1 FASTQ_URI]',
    'Comment[SRA_URI]']

    column_check = [col for col in expected_columns_ordered if col not in sdrf_2.columns]
    if column_check:
        print("Error: one or more expected columns is missing from sdrf.")
        print(column_check)
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
    optional_columns = [
    'Characteristics[developmental stage]',
    'Characteristics[sampling site]',
    'Characteristics[cell type]',
    'Characteristics[immunophenotype]',
    'Characteristics[stimulus]',
    'Characteristics[disease]',
    'Characteristics[organism status]',
    'Characteristics[cause of death]',
    'Comment[umi barcode read]',
    'Comment[umi barcode offset]',
    'Comment[umi barcode size]',
    'Comment[cell barcode read]',
    'Comment[cell barcode offset]',
    'Comment[cell barcode size]',
    'Comment[sample barcode read]',
    'Comment[sample barcode offset]',
    'Comment[sample barcode size]',
    'Comment[cDNA read]',
    'Comment[cDNA read offset]',
    'Comment[read1 FASTQ_URI]',
    'Comment[read2 FASTQ_URI]',
    'Comment[index1 file]',
    'Comment[index1 FASTQ_URI]',
    'Comment[SRA_URI]']

    for column_name in optional_columns:
        if set(list(sdrf_3[column_name])) == {''}:
            sdrf_3 = sdrf_3.drop([column_name], axis=1)

    '''How to display the dataframe during development.'''
    #pd.set_option("display.max_rows", None, "display.max_columns", None)
    #print(sdrf_3)

    '''Write the new sdrf file to a file.'''
    if not sdrf_3.empty:
        print(f"saving {work_dir}/{sdrf_file_name}")
        sdrf_3.to_csv(f"{work_dir}/{sdrf_file_name}", sep="\t", index=False)


def create_magetab(work_dir, tracking_sheet, xlsx_dict, dataset_protocol_map, df, args):

    accession_number = args.accession_number
    accession = f"E-HCAD-{accession_number}"

    idf_file_name = f"{accession}.idf.txt"
    sdrf_file_name = f"{accession}.sdrf.txt"

    generate_idf_file(work_dir, args, tracking_sheet, dataset_protocol_map, xlsx_dict, accession, idf_file_name,
                      sdrf_file_name)
    generate_sdrf_file(work_dir, args, df, dataset_protocol_map, sdrf_file_name)


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
        "-tt",
        "--technology_type",
        type=str,
        required=True,
        choices=['10Xv1_3','10Xv2_3','10Xv2_5','10Xv3_3','drop-seq','smart-seq','seq-well','smart-like'],
        help="Please indicate which single-cell sequencing technology was used."
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
        "--facs",
        action="store_true",
        default=None,
        help="Please specify this argument if FACS was used to isolate single cells"
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
        "-r",
        "--related_scea_accession",
        nargs='+',
        required=False,
        help="space separated list of related scea accession(s)"
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        required=False,
        help="Provide full path to preferred output dir"
    )

    args = parser.parse_args()
    if not args.output_dir:
        work_dir = f"script_spreadsheets/{os.path.splitext(os.path.basename(args.spreadsheet))[0]}"
    else:
        work_dir = args.output_dir

    tracking_sheet = utils.get_tracker_google_sheet()

    '''Merge the multitab spreadsheet into a single dataframe, while preserving the relationships
    between HCA biomaterials and protocols.
    '''
    xlsx_dict = multitab_excel_to_single_txt.multitab_excel_to_dict(work_dir, args.spreadsheet)
    merged_df = multitab_excel_to_single_txt.merge_dataframes(xlsx_dict)

    '''The merged df consists of a row per read index (read1, read2, index1). To conform to
    SCEA MAGE-TAB format, the rows should be merged by read pair including any index files.
    '''
    merged_df_by_reads = multitab_excel_to_single_txt.merge_rows_by_read_pair(merged_df)
    if ('index1' in merged_df['sequence_file.read_index'].values):
        merged_df_by_index = multitab_excel_to_single_txt.merge_index_reads(merged_df, merged_df_by_reads)
        clean_merged_df = multitab_excel_to_single_txt.clean_df(merged_df_by_index)
    else:
        clean_merged_df = multitab_excel_to_single_txt.clean_df(merged_df_by_reads)

    '''Extract the list of unique protocol ids from protocol types which can have more than one instance and
    creates extra columns in the df for each of the ids.'''
    df = multitab_excel_to_single_txt.create_new_protocol_columns(clean_merged_df, xlsx_dict)

    '''Create a map between the HCA protocol id and a new assigned SCEA protocol id. Use it to store the
    key protocol metadata that will be added to the SCEA sdrf file.'''
    dataset_protocol_map = get_protocol_map.prepare_protocol_map(xlsx_dict, df, args)

    '''Refactoring of the below TBD.'''
    create_magetab(work_dir, tracking_sheet, xlsx_dict, dataset_protocol_map, df, args)

if __name__ == '__main__':
    main()