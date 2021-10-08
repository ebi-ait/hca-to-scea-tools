import argparse
import json
import os
import pandas as pd

import multitab_excel_to_single_txt
import get_protocol_map
import fetch_fastq_path
import utils
from utils import (
    get_all_spreadsheets,
    map_proto_to_id,
    get_protocol_idf,
    convert_to_snakecase
    )

def reformat_tech(technology_type,FACS):
    if '10X' in technology_type:
        if FACS is None:
            single_cell_isolation = '10X'
        if '2' in technology_type:
            technology_type_reformatted = '10xV2'
        elif '3' in technology_type:
            technology_type_reformatted = '10xV3'
    else:
        technology_type_reformatted = technology_type
        if FACS is None:
            single_cell_isolation = technology_type
    if FACS is not None:
        single_cell_isolation = FACS
    return technology_type_reformatted,single_cell_isolation


def prepare_project_details(dataset_protocol_map, df, tracking_sheet, args):

    project_details = {}
    project_details = {"accession": args.accession_number, "curators": args.curators}
    # Save protocol columns for later use when creating sdrf.
    project_details['protocol_columns'] = get_protocol_map.map_of_hca_protocol_type_id_keys

    # Prepare project details to dump into file
    project_details['protocol_map'] = dataset_protocol_map
    project_details['project_uuid'] = args.project_uuid
    project_details['EAExperimentType'] = args.experiment_type
    project_details['hca_update_date'] = args.hca_update_date
    project_details['ExperimentalFactorName'] = args.experimental_factors
    project_details['related_scea_accession'] = args.related_scea_accession
    project_details['public_release_date'] = args.public_release_date

    accessions = utils.get_accessions_for_project(tracking_sheet, identifier=project_details['project_uuid'])
    if accessions:
        accessions_uniq = utils.get_unique_accessions([accessions])
        [accessions_uniq.remove(accession) for accession in accessions_uniq if 'HCAD' in accession.upper()]
        if accessions_uniq:
            project_details['secondary_accessions'] = accessions_uniq
        else:
            project_details['secondary_accessions'] = []
    else:
        project_details['secondary_accessions'] = []

    # Prepare configurable fields.
    biomaterial_id_columns = [x for x in df.columns if x.endswith("biomaterial_id") or x.endswith("biosamples_accession") or x.endswith("biomaterial_id") or x.endswith("insdc_run_accessions")]

    read_map = {'': "", 'Read 1': "read1", 'Read 2': "read2"}

    def get_or_default(source, default):
        return str(df[source].values[0]) if source in df.columns else default

    with open(f"technology_jsons/{args.technology_type}.json") as json_file:
        project_details['configurable_fields'] = json.load(json_file)

    project_details['name_field'] = args.name

    if args.facs is True:
        technology_type_reformatted,facs = reformat_tech(args.technology_type,'FACS')
    else:
        technology_type_reformatted,facs = reformat_tech(args.technology_type,None)
    project_details['technology_type'] = technology_type_reformatted
    project_details['single_cell_isolation'] = facs

    return project_details


def create_magetab(work_dir, xlsx_dict, df, project_details, args):

    accession_number = args.accession_number
    accession = f"E-HCAD-{accession_number}"
    idf_file_name = f"{accession}.idf.txt"
    sdrf_file_name = f"{accession}.sdrf.txt"

    tab = '\t'
    protocol_map = project_details['protocol_map']
    protocol_columns = project_details['protocol_columns']
    configurable_fields = project_details['configurable_fields']
    technology_type = project_details['technology_type']

    name_field = project_details['name_field']

    facs = project_details['single_cell_isolation']

    def generate_idf_file():
        protocol_fields = get_protocol_idf(protocol_map)

        def j(sheet, col_name, func=lambda x: x):
            return tab.join([func(p) for p in g(sheet, col_name)])

        def g(sheet, col_name):
            return list(xlsx_dict[sheet][col_name].fillna('').replace(r'[\n\r]', ' ', regex=True))

        def first_letter(str):
            return str[0] if len(str) else ''

        person_roles = g("project_contributors", "project.contributors.project_role.text")
        person_roles_submitter = g("project_contributors", "project.contributors.corresponding_contributor")

        for (i, elem) in enumerate(person_roles_submitter):
            person_roles[i] = person_roles[i].lower()
            if elem == "yes":
                person_roles[i] = "submitter"
            elif elem == "no":
                if "curator" in person_roles[i]:
                    person_roles[i] = "data curator"
                else:
                    person_roles[i] = ""

        if project_details.get('related_experiment'):

            idf_file_contents = f"""\

MAGE-TAB Version\t1.1
Investigation Title\t{g("project", "project.project_core.project_title")[0]}
Comment[Submitted Name]\t{g("project", "project.project_core.project_short_name")[0]}
Experiment Description\t{g("project", "project.project_core.project_description")[0]}
Public Release Date\t{project_details.get('public_release_date')}
Person First Name\t{j("project_contributors", "project.contributors.name", lambda x: x.split(',')[0])}
Person Last Name\t{j("project_contributors", "project.contributors.name", lambda x: x.split(',')[2])}
Person Mid Initials\t{j("project_contributors", "project.contributors.name", lambda x: first_letter(x.split(',')[1]))}
Person Email\t{j("project_contributors", "project.contributors.email")}
Person Affiliation\t{j("project_contributors", "project.contributors.institution")}
Person Address\t{j("project_contributors", "project.contributors.address")}
Person Roles\t{tab.join(person_roles)}
Protocol Type\t{tab.join([field[0] for field in protocol_fields])}
Protocol Name\t{tab.join([field[1] for field in protocol_fields])}
Protocol Description\t{tab.join([field[2] for field in protocol_fields])}
Protocol Hardware\t{tab.join([field[3] for field in protocol_fields])}
Term Source Name\tEFO\tArrayExpress
Term Source File\thttp://www.ebi.ac.uk/efo/efo.owl\thttp://www.ebi.ac.uk/arrayexpress/
Comment[AEExperimentType]\tRNA-seq of coding RNA from single cells
Experimental Factor Name\t{tab.join(project_details.get('ExperimentalFactorName'))}
Experimental Factor Type\t{tab.join(project_details.get('ExperimentalFactorName'))}
Comment[EAAdditionalAttributes]\t{''}
Comment[EACurator]\t{tab.join(project_details['curators'])}
Comment[EAExpectedClusters]\t
Comment[ExpressionAtlasAccession]\t{accession}
Comment[RelatedExperiment]\t{project_details.get('')}
Comment[HCALastUpdateDate]\t{project_details.get('hca_update_date')}
Comment[SecondaryAccession]\t{project_details['project_uuid']}\t{tab.join(project_details.get('secondary_accessions') or [])}
Comment[EAExperimentType]\t{project_details.get('EAExperimentType')}
SDRF File\t{sdrf_file_name}
"""
        else:
            idf_file_contents = f"""\

MAGE-TAB Version\t1.1
Investigation Title\t{g("project", "project.project_core.project_title")[0]}
Comment[Submitted Name]\t{g("project", "project.project_core.project_short_name")[0]}
Experiment Description\t{g("project", "project.project_core.project_description")[0]}
Public Release Date\t{project_details.get('public_release_date')}
Person First Name\t{j("project_contributors", "project.contributors.name", lambda x: x.split(',')[0])}
Person Last Name\t{j("project_contributors", "project.contributors.name", lambda x: x.split(',')[2])}
Person Mid Initials\t{j("project_contributors", "project.contributors.name", lambda x: first_letter(x.split(',')[1]))}
Person Email\t{j("project_contributors", "project.contributors.email")}
Person Affiliation\t{j("project_contributors", "project.contributors.institution")}
Person Address\t{j("project_contributors", "project.contributors.address")}
Person Roles\t{tab.join(person_roles)}
Protocol Type\t{tab.join([field[0] for field in protocol_fields])}
Protocol Name\t{tab.join([field[1] for field in protocol_fields])}
Protocol Description\t{tab.join([field[2] for field in protocol_fields])}
Protocol Hardware\t{tab.join([field[3] for field in protocol_fields])}
Term Source Name\tEFO\tArrayExpress
Term Source File\thttp://www.ebi.ac.uk/efo/efo.owl\thttp://www.ebi.ac.uk/arrayexpress/
Comment[AEExperimentType]\tRNA-seq of coding RNA from single cells
Experimental Factor Name\t{tab.join(project_details['ExperimentalFactorName'])}
Experimental Factor Type\t{tab.join(project_details['ExperimentalFactorName'])}
Comment[EAAdditionalAttributes]
Comment[EACurator]\t{tab.join(project_details['curators'])}
Comment[EAExpectedClusters]\t
Comment[ExpressionAtlasAccession]\t{accession}
Comment[HCALastUpdateDate]\t{project_details.get('hca_update_date')}
Comment[SecondaryAccession]\t{project_details['project_uuid']}\t{tab.join(project_details['secondary_accessions'] or [])}
Comment[EAExperimentType]\t{project_details.get('EAExperimentType')}
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

    def generate_sdrf_file(df,technology_type,facs,name_field,args):
    
        #
        ## SDRF Part.
        #

        df['UNDEFINED_FIELD'] = ''

        experiment_accessions = []
        for col in list(df.columns):
            if 'process' in col:
                bool = isinstance(list(df[col])[0], float)
                if bool is False:
                    if 'SRX' in list(df[col])[0]:
                        experiment_accessions = list(df[col])
        if not experiment_accessions:
            experiment_accessions = [''] * df.shape[0]

        biosample_accessions = list(df['cell_suspension.biomaterial_core.biosamples_accession'])

        convert_map_chunks = [{
            'Source Name': "UNDEFINED_FIELD",
            'Characteristics[organism]': "donor_organism.genus_species.ontology_label",
            'Characteristics[individual]': "donor_organism.biomaterial_core.biomaterial_id",
            'Characteristics[sex]': "donor_organism.sex",
            'Characteristics[age]': "donor_organism.organism_age",
            'Unit [time unit]': "donor_organism.organism_age_unit.text",
            'Characteristics[developmental stage]': "donor_organism.development_stage.text",
            'Characteristics[organism part]': "specimen_from_organism.organ.ontology_label",
            'Characteristics[sampling site]': "specimen_from_organism.organ_parts.ontology_label",
            'Characteristics[cell type]': "cell_suspension.selected_cell_types.ontology_label",
            'Characteristics[disease]': "donor_organism.diseases.ontology_label",
            'Characteristics[organism status]': "donor_organism.is_living",
            'Characteristics[cause of death]': "donor_organism.death.cause_of_death",
            'Characteristics[clinical history]': "donor_organism.medical_history.test_results",
            'Description': "specimen_from_organism.biomaterial_core.biomaterial_description",
            'Material Type_1': "UNDEFINED_FIELD",
        }, {
            'Protocol REF': "GENERIC_PROTOCOL_FIELD",
        }, {
            'Extract Name': "UNDEFINED_FIELD",
            'Material Type_2': "UNDEFINED_FIELD",
            'Comment[library construction]': technology_type,
            'Comment[input molecule]': "library_preparation_protocol.input_nucleic_acid_molecule.ontology_label",
            'Comment[primer]': "UNDEFINED_FIELD",
            'Comment[end bias]': "library_preparation_protocol.end_bias",
            'Comment[umi barcode read]': "UNDEFINED_FIELD",
            'Comment[umi barcode offset]': "UNDEFINED_FIELD",
            'Comment[umi barcode size]': "UNDEFINED_FIELD",
            'Comment[cell barcode read]': "UNDEFINED_FIELD",
            'Comment[cell barcode offset]': "UNDEFINED_FIELD",
            'Comment[cell barcode size]': "UNDEFINED_FIELD",
            'Comment[sample barcode read]': "UNDEFINED_FIELD",
            'Comment[sample barcode offset]': "UNDEFINED_FIELD",
            'Comment[sample barcode size]': "UNDEFINED_FIELD",
            'Comment[single cell isolation]': facs,
            'Comment[cDNA read]': "UNDEFINED_FIELD",
            'Comment[cDNA read offset]': "UNDEFINED_FIELD",
            'Comment[cDNA read size]': "UNDEFINED_FIELD",
            'Comment[LIBRARY_STRAND]': "library_preparation_protocol.strand",
            'Comment[LIBRARY_LAYOUT]': "UNDEFINED_FIELD",
            'Comment[LIBRARY_SOURCE]': "UNDEFINED_FIELD",
            'Comment[LIBRARY_STRATEGY]': "UNDEFINED_FIELD",
            'Comment[LIBRARY_SELECTION]': "UNDEFINED_FIELD",
        }, {
            'Protocol REF': "GENERIC_PROTOCOL_FIELD",
        }, {
            'Assay Name': "specimen_from_organism.biomaterial_core.biomaterial_id",
            'Technology Type': "UNDEFINED_FIELD",
            'Scan Name': "UNDEFINED_FIELD",
            'Comment[RUN]': "UNDEFINED_FIELD",
            'Comment[BioSD_SAMPLE]': '',
            'Comment[ENA_EXPERIMENT]': '',
            'Comment[read1 file]': "sequence_file.file_core.file_name_read1",
            'Comment[read2 file]': "sequence_file.file_core.file_name_read2",
            'Comment[index1 file]': "sequence_file.file_core.file_name_index1"
        }]

        def get_from_bigtable(column):
            return df[column] if column in df.columns else df['UNDEFINED_FIELD']

        # Chunk 1: donor info.
        sdrf_1 = pd.DataFrame({k: get_from_bigtable(v) for k, v in convert_map_chunks[0].items()})
        sdrf_1 = sdrf_1.fillna('')
        sdrf_1['Characteristics[age]'] = reformat_age(list(sdrf_1['Characteristics[age]']))

        # Fixes for chunk 1.
        # Organism status: convert from 'is_alive' to 'status'.
        sdrf_1['Characteristics[organism status]'] = sdrf_1['Characteristics[organism status]'].apply(lambda x: 'alive' if x.lower() in ['yes', 'y'] else 'dead')

        # Chunk 2: collection/dissociation/enrichment/library prep protocols
        def convert_term(term, name):
            return map_proto_to_id(term, protocol_map)

        def convert_row(row):
            return row.apply(lambda x: convert_term(x, row.name))

        protocols_for_sdrf_2 = ['collection_protocol', 'dissociation_protocol', 'enrichment_protocol', 'library_preparation_protocol']

        sdrf_2 = df[[col for (proto_type, cols) in protocol_columns.items() if proto_type in protocols_for_sdrf_2 for col in cols]]

        pd.set_option('display.max_columns', 0)
        pd.set_option('display.expand_frame_repr', False)

        sdrf_2 = sdrf_2.apply(convert_row)
        sdrf_2_list = []

        for (_, row) in sdrf_2.iterrows():
            short_row = list(set([x for x in row.tolist() if x != '']))
            short_row.sort()
            sdrf_2_list.append(short_row)

        sdrf_2 = pd.DataFrame.from_records(sdrf_2_list)
        sdrf_2.columns = ["Protocol REF" for col in sdrf_2.columns]
        sdrf_2.fillna(value='', inplace=True)

        # Chunk 3: Library prep protocol info
        sdrf_3 = pd.DataFrame({k: get_from_bigtable(v) for k, v in convert_map_chunks[2].items()})
        sdrf_3 = sdrf_3.fillna('')

        # Fixes for chunk 3:
        # In column Comment[input molecule], apply input_molecule_map.

        input_molecule_map = {'': "", 'polyA RNA extract': "polyA RNA", 'polyA RNA': "polyA RNA"}

        sdrf_3['Comment[library construction]'] = technology_type
        sdrf_3['Comment[single cell isolation]'] = facs
        sdrf_3['Comment[input molecule]'] = sdrf_3['Comment[input molecule]'].apply(lambda x: input_molecule_map[x])

        # Chunk 4: sequencing protocol ids.
        protocols_for_sdrf_4 = ['sequencing_protocol']

        sdrf_4 = df[[col for (proto_type, cols) in protocol_columns.items() if proto_type in protocols_for_sdrf_4 for col in cols]]
        sdrf_4 = sdrf_4.apply(convert_row)
        sdrf_4.columns = ["Protocol REF" for col in sdrf_4.columns]

        # Chunk 5: Sequence files.
        sdrf_5 = pd.DataFrame({k: get_from_bigtable(v) for k, v in convert_map_chunks[4].items()})

        # Merge all chunks.
        sdrf = sdrf_1.join(sdrf_2).join(sdrf_3, rsuffix="_1").join(sdrf_4, rsuffix="_1").join(sdrf_5)

        # Put in configurable fields.
        for field in configurable_fields:
            if field.get('type', None) == "column":
                sdrf[field['name']] = get_from_bigtable(field['value'])
            else:
                sdrf[field['name']] = field['value']

        # fixes to sample name fields

        if name_field == 'cs_name':
            name = list(df['cell_suspension.biomaterial_core.biomaterial_name'])
        elif name_field == 'cs_id':
            name = list(df['cell_suspension.biomaterial_core.biomaterial_id'])
        elif name_field == 'sp_name':
            name = list(df['specimen_from_organism.biomaterial_core.biomaterial_name'])
        elif name_field == 'sp_id':
            name = list(df['specimen_from_organism.biomaterial_core.biomaterial_id'])

        sdrf['Source Name'] = name
        sdrf['Scan Name'] = name
        sdrf['Comment[RUN]'] = name
        sdrf['Assay Name'] = name
        sdrf['Extract Name'] = name

        # fixes to ena experiment and biosample fields
        sdrf['Comment[ENA_EXPERIMENT]'] = experiment_accessions
        sdrf['Comment[BioSD_SAMPLE]'] = biosample_accessions

        # Fix column names.
        sdrf = sdrf.rename(columns = {'Protocol REF_1' : "Protocol REF", 'Material Type_1': "Material Type", 'Material Type_2': "Material Type"})

        # get fastq file paths from ENA or SRA database
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
            print("Found paths to SRA Object files in NCBI SRA database. Entering those in place of fastq file paths.")
        except:
            print("Could not obtain fastq file paths or SRA file paths. Please record a ticket with the input arguments"
                  "and enter them manually.")

        if not sdrf.empty:
            print(f"saving {work_dir}/{sdrf_file_name}")
            sdrf.to_csv(f"{work_dir}/{sdrf_file_name}", sep="\t", index=False)

    generate_idf_file()

    generate_sdrf_file(df,technology_type,facs,name_field,args)

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
    project_details = prepare_project_details(dataset_protocol_map, df,
                                              tracking_sheet, args)

    '''Refactoring of the below TBD.'''
    create_magetab(work_dir, xlsx_dict, df, project_details, args)

if __name__ == '__main__':
    main()
