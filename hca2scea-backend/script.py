import argparse
import sys
import json
import os
from pathlib import Path
import requests as rq
from xml.etree import ElementTree

import numpy as np
import pandas as pd # can probably use openpyxl directly

from utils import tracker
from utils import protocol
from utils import helper

# Get protocol types from protocol map.
def get_protocol_idf(protocol_map):
    proto_types = [protocol.protocol_type_map[protocol_type] for (protocol_type, value) in protocol_map.items() for repeats in range(len(value.keys()))]
    proto_names = [protocol['scea_id'] for (protocol_type, protocols) in protocol_map.items() for (protocol_name, protocol) in protocols.items()]
    proto_descs = [protocol['description'] for (protocol_type, protocols) in protocol_map.items() for (protocol_name, protocol) in protocols.items()]
    proto_hware = [protocol.get('hardware', '') for (protocol_type, protocols) in protocol_map.items() for (protocol_name, protocol) in protocols.items()]
    return list(zip(proto_types, proto_names, proto_descs, proto_hware))

def extract_multiprotocols(tabs_dict, merged_tabs):
    for (protocol_type, protocol_field) in protocol.multiprotocols.items():
        if tabs_dict.get(protocol_type) is not None:
            tabs_dict[protocol_type] = tabs_dict[protocol_type].fillna('')
            proto_df, proto_df_columns = protocol.split_multiprotocols(merged_tabs, protocol_field)
            for proto_column in proto_df_columns:
                if protocol.protocol_columns.get(protocol_type) == None:
                    protocol.protocol_columns[protocol_type] = []
                protocol.protocol_columns[protocol_type].append(proto_column)
            for column_name in proto_df.columns:
                merged_tabs[column_name] = list(proto_df[column_name])
    return merged_tabs

def parse_xml(xml_content):
    for experiment_package in xml_content.findall('EXPERIMENT_PACKAGE'):
        yield experiment_package

def filter_paths(sdrf,paths):
    runs = list(sdrf['Comment[ENA_RUN]'])
    read1_files = []
    read2_files = []
    index1_files = []
    index2_files = []
    sra_files = []
    bam_files = []
    read1_paths = []
    read2_paths = []
    index1_paths = []
    index2_paths = []
    sra_paths = []
    bam_paths = []
    for i in range(0,len(runs)):
        run = runs[i]
        if paths[run]['filetype'] == 'fastq file':
            if 'read1' in paths[run]['filename'].keys():
                read1_files.append(paths[run]['filename']['read1'])
                read1_paths.append(paths[run]['filepath']['read1'])
            elif 'read2' in paths[run]['filename'].keys():
                read2_files.append(paths[run]['filename']['read2'])
                read2_paths.append(paths[run]['filepath']['read2'])
            elif 'index1' in paths[run]['filename'].keys():
                index1_files.append(paths[run]['filename']['index1'])
                index1_paths.append(paths[run]['filepath']['index1'])
            elif 'read2' in paths[run]['filename'].keys():
                index2_files.append(paths[run]['filename']['index2'])
                index2_paths.append(paths[run]['filepath']['index2'])
        else:
            if paths[run]['filetype'] == 'SRA Object':
                sra_files.append(paths[run]['filename'])
                sra_paths.append(paths[run]['filepath'])
            elif paths[run]['filetype'] == 'BAM file':
                bam_files.append(paths[run]['filename'])
                bam_paths.append(paths[run]['filepath'])
    if read1_files:
        sdrf['Comment[read1 file]'] = read1_files
        sdrf['Comment[read1 FASTQ_URI]'] = read1_paths
    if read2_files:
        sdrf['Comment[read2 file]'] = read2_files
        sdrf['Comment[read2 FASTQ_URI]'] = read2_paths
    if index1_files:
        sdrf['Comment[index1 file]'] = index1_files
        sdrf['Comment[index1 FASTQ_URI]'] = index1_paths
    if index2_files:
        sdrf['Comment[index2 file]'] = index2_files
        sdrf['Comment[index2 FASTQ_URI]'] = index2_paths
    if not read1_files:
        sdrf.drop('Comment[read1 file]',inplace=True, axis=1)
        sdrf.drop('Comment[read2 file]',inplace=True, axis=1)
        sdrf.drop('Comment[index1 file]',inplace=True, axis=1)
        if sra_files:
            sdrf['Comment[SRA file]'] = sra_files
            sdrf['Comment[SRA path]'] = sra_paths
        elif sra_files:
            sdrf['Comment[BAM file]'] = bam_files
            sdrf['Comment[BAM path]'] = bam_paths
    sdrf.drop_duplicates(keep=False, inplace=True)
    return sdrf

def check_file_types(paths):
    for accession in paths.keys():
        fastq = [path for path in paths[accession]['files'] if 'fastq.gz' in path]
        if fastq and len(fastq) > 1:
            for file in fastq:
                if 'R1' in file or '_1' in file:
                    paths[accession].update({'filename':{'read1':os.path.basename(file)}})
                    paths[accession].update({'filepath':{'read1': file}})
                elif 'R2' in file or '_2' in file:
                    paths[accession].update({'filename': {'read2': os.path.basename(file)}})
                    paths[accession].update({'filepath': {'read2': file}})
                elif 'I1' in file or '_3' in file:
                    paths[accession].update({'filename': {'index1': os.path.basename(file)}})
                    paths[accession].update({'filepath': {'index1': file}})
                else:
                    paths[accession].update({'filename': {'index2': os.path.basename(file)}})
                    paths[accession].update({'filepath': {'index2': file}})
                paths[accession]['filetype'] = 'fastq file'
        elif not fastq or len(fastq) < 2:
            paths[accession].update({'filepath':paths[accession]['files'][0]})
            paths[accession].update({'filename':os.path.basename(paths[accession]['files'][0])})
            if paths[accession]['filename'] == accession:
                paths[accession].update({'filetype':'SRA Object'})
            elif 'bam' in paths[accession]['filename']:
                paths[accession].update({'filetype':'BAM file'})
            else:
                paths[accession].update({'filetype':'unknown'})
    return paths

def get_fastq_path_from_sra(sdrf):
    run_accessions = list(sdrf['Comment[ENA_RUN]'])
    url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch/fcgi?db=sra&id={",".join(run_accessions)}'
    srr_metadata_url = rq.get(url)
    paths = {}
    tree = ElementTree.fromstring(srr_metadata_url.content)
    try:
        for experiment_package in tree.findall('EXPERIMENT_PACKAGE'):
            for run in experiment_package.find('RUN_SET'):
                attributes = run.find('SRAFiles')
                for sra_file in attributes:
                    accession = sra_file.attrib['filename']
                    paths[accession] = {'files':[]}
                    for attrib in sra_file:
                        url = attrib.attrib['url']
                        paths[accession]['files'].append(url)
    except:
        paths = None
    return paths

def get_fastq_path_from_ena(study_accession,sra_paths):
    try:
        request_url = f'http://www.ebi.ac.uk/ena/data/warehouse/filereport?accession={study_accession}&result=read_run&fields=run_accession,fastq_ftp'
        fastq_results = pd.read_csv(request_url, delimiter='\t')
        if fastq_results.shape[0] > 0:
            for i in range(0,len(list(fastq_results['run_accession']))):
                accession = list(fastq_results['run_accession'])[i]
                if accession in sra_paths.keys():
                    sra_paths[accession] = {'files':[]}
                    sra_paths[accession]['files'].append(list(fastq_results['fastq_ftp'])[i])
                else:
                    continue
            paths = sra_paths
    except:
        paths = sra_paths
    return paths

def merge(tab1, tab2, key):
    cols = tab2.columns.values.tolist() + tab1.columns.values.tolist()
    rows = []
    for i in range(0,tab1.shape[0]):
        row_values1 = tab1.loc[i].values.tolist()
        key_value = list(tab1[key])[i]
        row_values2 = tab2[tab2[key] == key_value].values[0].tolist()
        rows.append(row_values2 + row_values1)
    df = pd.DataFrame(rows,columns=cols)
    return df

def merge_tabs(work_dir, tabs_dict):

    df1 = merge(tab1=tabs_dict['sequence_file'], tab2=tabs_dict['cell_suspension'], key='cell_suspension.biomaterial_core.biomaterial_id')
    df2 = merge(tab1=df1, tab2=tabs_dict['specimen_from_organism'], key='specimen_from_organism.biomaterial_core.biomaterial_id')
    df3 = merge(tab1=df2, tab2=tabs_dict['donor_organism'], key='donor_organism.biomaterial_core.biomaterial_id')
    df4 = merge(tab1=df3, tab2=tabs_dict['library_preparation_protocol'], key='library_preparation_protocol.protocol_core.protocol_id')
    df5 = merge(tab1=df4, tab2=tabs_dict['sequencing_protocol'], key='sequencing_protocol.protocol_core.protocol_id')
    merged_tabs = df5

    # Remove NAs in protocol spreadsheets.
    for protocol_type in protocol.protocol_columns.keys():
        tabs_dict[protocol_type] = tabs_dict[protocol_type].fillna('')

    # Extract the lists from protocol types which can have more than one instance and creates extra columns in the
    # merged_tabs df for each of the items, as well as the count and the python-style list.
    merged_tabs = extract_multiprotocols(tabs_dict, merged_tabs)

    # Saving merged_tabs dataframe as a single .csv file.
    merged_tabs.to_csv(f"{work_dir}/merged_tabs.csv", index=False, sep=";")

    return merged_tabs

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

def prepare_protocol_map(merged_tabs, tabs_dict, project_details):

    '''
    Get the prefix for the protocol ids using the accession number.
    '''
    accession_number = project_details["accession"].split("-")[-1]
    protocol_accession = f"HCAD{accession_number}"

    # Save protocol columns for later use when creating sdrf.
    project_details['protocol_columns'] = protocol.protocol_columns

    # First, we prepare an ID minter for the protocols following SCEA MAGE-TAB standards.
    protocol_id_counter = 0

    # Then, protocol map is created: a dict containing types of protocols, and inside each, a map from HCA ids to SCEA ids.
    protocol_map = {x: {} for x in protocol.protocol_order}
    for proto_type in protocol.protocol_order:
        key = proto_type + ".protocol_core.protocol_id"
        proto_type_columns = protocol.get_proto_type_columns(merged_tabs, key)
        proto_type_values = protocol.get_proto_type_values(merged_tabs, key, proto_type_columns)
        for proto_type_value in proto_type_values:
            protocol_id_counter += 1
            new_proto_id = f"P-{protocol_accession}-{protocol_id_counter}"
            protocol_map[proto_type].update({proto_type_value: {'scea_id': new_proto_id, 'hca_ids': [proto_type_value]}})

    # Using that function, we get the description for all protocol types, and the hardware for sequencing protocols into
    # the map.
    protocol.extract_protocol_description(protocol_map, tabs_dict, f"protocol_core.protocol_description", "description")
    protocol.extract_protocol_description(protocol_map, tabs_dict, f"instrument_manufacturer_model.ontology_label", "hardware", ["sequencing_protocol"])

    return protocol_map

def prepare_project_details(project_details, args):

    '''
    Get the list of project level secondary accessions for the MAGE-TAB files.
    '''
    accessions = tracker.get_accessions_for_project(tracker.get_tracker_google_sheet(), identifier=args.project_uuid)
    if accessions:
        project_details['secondary_accessions'] = tracker.get_project_accessions(accessions)
    else:
        project_details['secondary_accessions'] = []

    '''
    Get configurable technology type related fields from appropriate technology_json file.
    '''
    with open(f"technology_jsons/{args.technology_type}.json") as json_file:
        project_details['configurable_fields'] = json.load(json_file)

    '''
    Save the reformatted technoloy type and single cell isolation method in project_details dict.
    '''
    if args.facs is True:
        technology_type_reformatted,facs = reformat_tech(args.technology_type,'FACS')
    else:
        technology_type_reformatted,facs = reformat_tech(args.technology_type,None)
    project_details['technology_type'] = technology_type_reformatted
    project_details['single_cell_isolation'] = facs

    return project_details

def correct_person_roles(person_roles, person_roles_submitter):
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

def generate_idf_file(work_dir, tabs_dict, protocol_map, project_details, idf_file_name, sdrf_file_name, args, accession):

    '''
    Retrieve the required experimental protocol information from the protocol map.
    '''
    protocol_fields = get_protocol_idf(protocol_map)

    '''
    Retrieve and correct the contributors person roles to meet SCEA requirements.
    '''
    person_roles = helper.get_list_from_dict(dict=tabs_dict, tab="project_contributors", key="project.contributors.project_role.text")
    person_roles_submitter = helper.get_list_from_dict(dict=tabs_dict, tab="project_contributors", key="project.contributors.corresponding_contributor")
    person_roles = correct_person_roles(person_roles, person_roles_submitter)

    '''
    Write the MAGE-TAB idf file as an f string. The expressions inside brackets are evaluated at run time.
    '''

    tab = '\t'

    if args.related_scea_accession:

        idf_file_contents = f"""\

MAGE-TAB Version\t1.1
Investigation Title\t{helper.get_list_from_dict(dict=tabs_dict, tab="project", key="project.project_core.project_title")[0]}
Comment[Submitted Name]\t{helper.get_list_from_dict(dict=tabs_dict,tab="project", key="project.project_core.project_short_name")[0]}
Experiment Description\t{helper.get_list_from_dict(dict=tabs_dict, tab="project", key="project.project_core.project_description")[0]}
Public Release Date\t{args.public_release_date}
Person First Name\t{helper.get_tab_separated_list_from_dict(dict=tabs_dict, tab="project_contributors", key="project.contributors.name", func=lambda x: x.split(',')[0])}
Person Last Name\t{helper.get_tab_separated_list_from_dict(dict=tabs_dict, tab="project_contributors", key="project.contributors.name", func=lambda x: x.split(',')[2])}
Person Mid Initials\t{helper.get_tab_separated_list_from_dict(dict=tabs_dict, tab="project_contributors", key="project.contributors.name", func=lambda x: helper.get_first_letter(x.split(',')[1]))}
Person Email\t{helper.get_tab_separated_list_from_dict(dict=tabs_dict, tab="project_contributors", key="project.contributors.email")}
Person Affiliation\t{helper.get_tab_separated_list_from_dict(dict=tabs_dict, tab="project_contributors", key="project.contributors.institution")}
Person Address\t{helper.get_tab_separated_list_from_dict(dict=tabs_dict, tab="project_contributors", key="project.contributors.address")}
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
Comment[SecondaryAccession]\t{args.project_uuid}\t{tab.join(project_details.get('secondary_accessions') or [])}
Comment[EAExperimentType]\t{args.experiment_type}
SDRF File\t{sdrf_file_name}
"""
    else:
        idf_file_contents = f"""\

MAGE-TAB Version\t1.1
Investigation Title\t{helper.get_list_from_dict(dict=tabs_dict, tab="project", key="project.project_core.project_title")[0]}
Comment[Submitted Name]\t{helper.get_list_from_dict(dict=tabs_dict, tab="project", key="project.project_core.project_short_name")[0]}
Experiment Description\t{helper.get_list_from_dict(dict=tabs_dict, tab="project", key="project.project_core.project_description")[0]}
Public Release Date\t{args.public_release_date}
Person First Name\t{helper.get_tab_separated_list_from_dict(dict=tabs_dict, tab="project_contributors", key="project.contributors.name", func=lambda x: x.split(',')[0])}
Person Last Name\t{helper.get_tab_separated_list_from_dict(dict=tabs_dict, tab="project_contributors", key="project.contributors.name", func=lambda x: x.split(',')[2])}
Person Mid Initials\t{helper.get_tab_separated_list_from_dict(dict=tabs_dict, tab="project_contributors", key="project.contributors.name", func=lambda x: helper.get_first_letter(x.split(',')[1]))}
Person Email\t{helper.get_tab_separated_list_from_dict(dict=tabs_dict, tab="project_contributors", key="project.contributors.email")}
Person Affiliation\t{helper.get_tab_separated_list_from_dict(dict=tabs_dict, tab="project_contributors", key="project.contributors.institution")}
Person Address\t{helper.get_tab_separated_list_from_dict(dict=tabs_dict, tab="project_contributors", key="project.contributors.address")}
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
Comment[SecondaryAccession]\t{args.project_uuid}\t{tab.join(project_details['secondary_accessions'] or [])}
Comment[EAExperimentType]\t{args.experiment_type}
SDRF File\t{sdrf_file_name}
"""

    print(f"saving {work_dir}/{idf_file_name}")
    with open(f"{work_dir}/{idf_file_name}", "w") as idf_file:
        idf_file.write(idf_file_contents)

def generate_sdrf_file(project_details, args):

        #
        ## SDRF Part.
        #

        merged_tabs['UNDEFINED_FIELD'] = ''

        experiment_accessions = []
        for col in list(merged_tabs.columns):
            if 'process' in col:
                bool = isinstance(list(merged_tabs[col])[0], float)
                if bool is False:
                    if 'SRX' in list(merged_tabs[col])[0]:
                        experiment_accessions = list(merged_tabs[col])
        if not experiment_accessions:
            experiment_accessions = [''] * merged_tabs.shape[0]

        biosample_accessions = list(merged_tabs['cell_suspension.biomaterial_core.biosamples_accession'])

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
            'Comment[library construction]': project_details['technology_type'],
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
            'Comment[single cell isolation]': project_details['single_cell_isolation'],
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

        def get_from_merged_tabs(column):
            return merged_tabs[column] if column in merged_tabs.columns else merged_tabs['UNDEFINED_FIELD']

        # Chunk 1: donor info.
        sdrf_1 = pd.DataFrame({k: get_from_merged_tabs(v) for k, v in convert_map_chunks[0].items()})
        sdrf_1 = sdrf_1.fillna('')
        sdrf_1['Characteristics[age]'] = helper.replace_dash_with_to(list(sdrf_1['Characteristics[age]']))

        # Fixes for chunk 1.
        # Organism status: convert from 'is_alive' to 'status'.
        sdrf_1['Characteristics[organism status]'] = sdrf_1['Characteristics[organism status]'].apply(
            lambda x: 'alive' if x.lower() in ['yes', 'y'] else 'dead')

        # Chunk 2: collection/dissociation/enrichment/library prep protocols
        def convert_term(term, name):
            return protocol.map_proto_to_id(term, protocol_map)

        def convert_row(row):
            return row.apply(lambda x: convert_term(x, row.name))

        protocols_for_sdrf_2 = ['collection_protocol', 'dissociation_protocol', 'enrichment_protocol',
                                'library_preparation_protocol']

        sdrf_2 = merged_tabs[
            [col for (proto_type, cols) in protocol_columns.items() if proto_type in protocols_for_sdrf_2 for col in
             cols]]

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
        sdrf_3 = pd.DataFrame({k: get_from_merged_tabs(v) for k, v in convert_map_chunks[2].items()})
        sdrf_3 = sdrf_3.fillna('')

        # Fixes for chunk 3:
        # In column Comment[input molecule], apply input_molecule_map.

        input_molecule_map = {'': "", 'polyA RNA extract': "polyA RNA", 'polyA RNA': "polyA RNA"}
        sdrf_3['Comment[input molecule]'] = sdrf_3['Comment[input molecule]'].apply(lambda x: input_molecule_map[x])

        # Chunk 4: sequencing protocol ids.
        protocols_for_sdrf_4 = ['sequencing_protocol']

        sdrf_4 = merged_tabs[
            [col for (proto_type, cols) in protocol_columns.items() if proto_type in protocols_for_sdrf_4 for col in
             cols]]
        sdrf_4 = sdrf_4.apply(convert_row)
        sdrf_4.columns = ["Protocol REF" for col in sdrf_4.columns]

        # Chunk 5: Sequence files.
        sdrf_5 = pd.DataFrame({k: get_from_merged_tabs(v) for k, v in convert_map_chunks[4].items()})

        # Merge all chunks.
        sdrf = sdrf_1.join(sdrf_2).join(sdrf_3, rsuffix="_1").join(sdrf_4, rsuffix="_1").join(sdrf_5)

        # Put in configurable fields.
        for field in configurable_fields:
            if field.get('type', None) == "column":
                sdrf[field['name']] = get_from_merged_tabs(field['value'])
            else:
                sdrf[field['name']] = field['value']

        # fixes to sample name fields

        if args.name == 'cs_name':
            name = list(merged_tabs['cell_suspension.biomaterial_core.biomaterial_name'])
        elif args.name == 'cs_id':
            name = list(merged_tabs['cell_suspension.biomaterial_core.biomaterial_id'])
        elif args.name == 'sp_name':
            name = list(merged_tabs['specimen_from_organism.biomaterial_core.biomaterial_name'])
        elif args.name == 'sp_id':
            name = list(merged_tabs['specimen_from_organism.biomaterial_core.biomaterial_id'])

        sdrf['Source Name'] = name
        sdrf['Scan Name'] = name
        sdrf['Comment[RUN]'] = name
        sdrf['Assay Name'] = name
        sdrf['Extract Name'] = name

        # fixes to ena experiment and biosample fields
        sdrf['Comment[ENA_EXPERIMENT]'] = experiment_accessions
        sdrf['Comment[BioSD_SAMPLE]'] = biosample_accessions

        # Fix column names.
        sdrf = sdrf.rename(columns={'Protocol REF_1': "Protocol REF", 'Material Type_1': "Material Type",
                                    'Material Type_2': "Material Type"})

        paths = get_fastq_path_from_sra(sdrf)
        paths = get_fastq_path_from_ena(args.study, paths)
        paths = check_file_types(paths)
        sdrf = filter_paths(sdrf, paths)

        # Save SDRF file..
        print(f"saving {work_dir}/{sdrf_file_name}")
        sdrf.to_csv(f"{work_dir}/{sdrf_file_name}", sep="\t", index=False)

    generate_sdrf_file(project_details, args)

def create_magetab(work_dir, tabs_dict, protocol_map, project_details, merged_tabs, args):

    '''
    Create a name for the MAGE-TAB files using the newly assigned E-HCAD accession.
    '''
    accession_number = project_details['accession']
    accession = f"E-HCAD-{accession_number}"
    idf_file_name = f"{accession}.idf.txt"
    sdrf_file_name = f"{accession}.sdrf.txt"

    '''
    Create and write MAGE-TAB idf file.
    '''
    generate_idf_file(work_dir, tabs_dict, protocol_map, project_details, idf_file_name, sdrf_file_name, args, accession)

    '''
    Create and write MAGE-TAB sdrf file.
    '''
    generate_sdrf_file(work_dir, tabs_dict, protocol_map, project_details, idf_file_name, sdrf_file_name, args, accession)

def extract_csv_from_spreadsheet(work_dir, excel_file):
    xlsx = pd.ExcelFile(excel_file, engine='openpyxl')
    print("Converting sheets in excel file to dataframes...")
    d = {}
    for sheet in xlsx.sheet_names:
        path = Path(work_dir)
        path.mkdir(parents=True, exist_ok=True)
        filename = f"{helper.convert_to_snakecase(sheet)}"
        df = pd.read_excel(excel_file, sheet_name=sheet, header=0, skiprows=[0,1,2,4], engine='openpyxl').replace('', np.nan).dropna(how="all")
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        d[filename] = df
    print(f"{len(xlsx.sheet_names)} sheets converted to dataframes")
    return d

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
        type=str,
        required=False,
        help="Optionally add an E-HCAD accession number. If not provided, the script will automatically detect the next accession in order by querying the google tracker sheet"
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

    '''
    Create output directory if it does not already exist.
    '''
    if not args.output_dir:
        work_dir = f"script_spreadsheets/{os.path.splitext(os.path.basename(args.spreadsheet))[0]}"
    else:
        work_dir = args.output_dir

    '''
    Determine the next E-HCAD ID from the wrangler google tracker sheet if it is not provided as an argument.
    '''
    if args.accession_number:
        accession_number = args.accession_number
    else:
        accession_number = tracker.get_next_accession()

    '''
    Initialise a dictionary to store the E-HCAD ID accession number and curator initials.
    '''
    project_details = {"accession": accession_number}

    '''
    Extract each tab from an input multi-tab spreadsheet into separate pandas dataframes and then merge the dataframes
    into a single dataframe.
    '''
    tabs_dict = extract_csv_from_spreadsheet(work_dir, args.spreadsheet)
    merged_tabs = merge_tabs(work_dir, tabs_dict)

    '''
    Prepare a map of the protocol information derived from the extracted spreadsheets.
    '''
    protocol_map = prepare_protocol_map(merged_tabs, tabs_dict, project_details)

    '''
    Prepare project details to be entered into the MAGE-TAB files.
    '''
    project_details = prepare_project_details(project_details, args)

    '''
    Create MAGE-TAB and write files using the protocol map, project details dict and extracted spreadsheet tabs.
    '''
    create_magetab(work_dir, tabs_dict, protocol_map, project_details, merged_tabs, args)

if __name__ == '__main__':
    main()
