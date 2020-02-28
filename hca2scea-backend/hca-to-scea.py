#!/usr/bin/env python

# Disclaimer for brave explorers:
# This script is pulled directly from the Jupyter Notebook used to fix the data,
# so the code is not exactly organized in a manner that makes any sense.
# This process must be streamlined and refactored into something more clear.

import dateutil.parser
import glob
import json
import re
import sys
from os.path import basename, splitext

import pandas as pd
import requests


work_dir = sys.argv[1]

with open(f"./{work_dir}/info.json") as info_file:
    arg_dict = json.load(info_file)

print(arg_dict)

accession_index = arg_dict['accession']
curators = arg_dict['curators']

force_project_uuid = arg_dict.get("forced_project_uuid", None)

accession = f"E-HCAD-{accession_index}"
protocol_accession = f"HCAD{accession_index}"
idf_file_name = f"./{work_dir}/{accession}.idf.txt"
sdrf_file_name = f"./{work_dir}/{accession}.sdrf.txt"
fill_this_label = "<FILL THIS>"


## Helper functions ##
def convert_to_snakecase(label):
    return re.sub(r'(\s-\s)|\s', '_', label).lower()


def get_all_spreadsheets(work_dir):
    file_names = glob.glob(f"{work_dir}/*.csv")
    file_names = [x for x in file_names if not 'big_table.csv' in x]

    spreadsheets = {}

    for file_name in file_names:
        spreadsheets[convert_to_snakecase(splitext(basename(file_name))[0])] = file_name

    return spreadsheets


## Main Script ##

# Load all spreadsheets
spreadsheets = get_all_spreadsheets(work_dir)

for name, file_name in spreadsheets.items():
    newSheet = pd.read_csv(file_name, header=0, sep=";", skiprows=[0,1,2,4])
    spreadsheets[name] = newSheet.loc[:, ~newSheet.columns.str.contains('^Unnamed')]

big_table = None

# Merge sequence files with cell suspensions
big_table = spreadsheets['cell_suspension'].merge(
    spreadsheets['sequence_file'],
    how="outer",
    on="cell_suspension.biomaterial_core.biomaterial_id"
)

# Take specimen ids from cell suspensions if there are any.
def get_specimen(cell_line_id):
    return spreadsheets['cell_line'].loc[spreadsheets['cell_line']['cell_line.biomaterial_core.biomaterial_id'] == cell_line_id]['specimen_from_organism.biomaterial_core.biomaterial_id'].values[0]

if 'cell_line' in spreadsheets.keys():
    big_table['specimen_from_organism.biomaterial_core.biomaterial_id'] = big_table['specimen_from_organism.biomaterial_core.biomaterial_id'].fillna(big_table.loc[big_table['specimen_from_organism.biomaterial_core.biomaterial_id'].isna()]['cell_line.biomaterial_core.biomaterial_id'].apply(get_specimen))

# Merge specimens into big table
big_table = spreadsheets['specimen_from_organism'].merge(
    big_table,
    how="outer",
    on="specimen_from_organism.biomaterial_core.biomaterial_id"
)

# Merge donor organisms into big table
big_table = spreadsheets['donor_organism'].merge(
    big_table,
    how="outer",
    on="donor_organism.biomaterial_core.biomaterial_id"
)

# Merge library preparation and sequencing protocols into big table
big_table = spreadsheets['library_preparation_protocol'].merge(
    big_table,
    how="outer",
    on="library_preparation_protocol.protocol_core.protocol_id"
)

big_table = spreadsheets['sequencing_protocol'].merge(
    big_table,
    how="outer",
    on="sequencing_protocol.protocol_core.protocol_id"
)


# Merge the two rows for each read (read1 and read2)
big_table_read1 = big_table.loc[big_table['sequence_file.read_index'] == 'read1']
big_table_read2 = big_table.loc[big_table['sequence_file.read_index'] == 'read2']

big_table_read2_short = big_table_read2[[
    'cell_suspension.biomaterial_core.biomaterial_id',
    'sequence_file.file_core.file_name',
    'sequence_file.read_length',
    'sequence_file.lane_index',
]]

big_table_joined = big_table_read1.merge(
    big_table_read2_short,
    on=['cell_suspension.biomaterial_core.biomaterial_id', 'sequence_file.lane_index'],
    suffixes=("_read1", "_read2")
)

if ('index1' in big_table['sequence_file.read_index'].values):
    # Merge index rows for each read
    big_table = big_table.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    big_table_index1 = big_table.loc[big_table['sequence_file.read_index'] == 'index1']

    big_table_index1_short = big_table_index1[[
        'cell_suspension.biomaterial_core.biomaterial_id',
        'sequence_file.file_core.file_name',
        'sequence_file.read_length',
        'sequence_file.lane_index',
    ]]

    big_table_index1_short.columns = [f"{x}_index1" for x in big_table_index1_short.columns]

    big_table_joined2 = big_table_joined.merge(
        big_table_index1_short,
        left_on=['cell_suspension.biomaterial_core.biomaterial_id', 'sequence_file.lane_index'],
        right_on=["cell_suspension.biomaterial_core.biomaterial_id_index1", 'sequence_file.lane_index_index1'],
    )

    big_table_joined = big_table_joined2

big_table_joined.reset_index(inplace=True)
big_table_joined = big_table_joined.rename(columns={'sequence_file.file_core.file_name': 'sequence_file.file_core.file_name_read1'})
big_table_joined_sorted = big_table_joined.reindex(sorted(big_table_joined.columns), axis=1)
big_table_joined_sorted = big_table_joined_sorted.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
big_table = big_table_joined_sorted


# Mapping Protocols
protocol_type_map = {
    'collection_protocol': "sample collection protocol",
    'dissociation_protocol': "enrichment protocol",
    '??????????????????????': "nucleic acid extraction protocol",
    'enrichment_protocol': "enrichment_protocol",
    'library_preparation_protocol': "nucleic acid library construction protocol",
    'sequencing_protocol': "nucleic acid sequencing protocol",
}

protocol_order = [
    'collection_protocol',
    'dissociation_protocol',
    'enrichment_protocol',
    'library_preparation_protocol',
    'sequencing_protocol',
]

protocol_columns = [
    ('collection_protocol', 'collection_protocol.protocol_core.protocol_id'),
    ('library_preparation_protocol', 'library_preparation_protocol.protocol_core.protocol_id'),
    ('sequencing_protocol', 'sequencing_protocol.protocol_core.protocol_id'),
]

for (protocol_type, _) in protocol_columns:
    spreadsheets[protocol_type] = spreadsheets[protocol_type].fillna('')

def map_proto_to_id(protocol_name):
    for _, proto in protocol_map.items():
        if protocol_name in proto:
            return proto.get(protocol_name)['id']
    return ''


# Extract lists of protocols
# Helpers to convert lists in HCA spreadsheets (items are separated with two pipes `||`) to python lists.
def splitlist(list_):
    split_data = []
    try:
        split_data = list_.split('||')
    except:
        pass

    return split_data

def split_multiprotocols(df, proto_column):
    proto_series = df[proto_column].apply(splitlist)
    proto_df = pd.DataFrame(proto_series.values.tolist())
    proto_df_columns = [f'{proto_column}_{y}' for y in range(len(proto_df.columns))]
    proto_df.columns = proto_df_columns
    proto_df[f'{proto_column}_count'] = proto_series.str.len()
    proto_df[f'{proto_column}_list'] = proto_series

    return (proto_df, proto_df_columns)

# This extracts the lists from protocol types which can have more than one instance and creates extra columns in the
# Big Table for each of the items, as well as the count and the python-style list.
multiprotocols = [
    ('dissociation_protocol', 'dissociation_protocol.protocol_core.protocol_id'),
    ('enrichment_protocol', 'enrichment_protocol.protocol_core.protocol_id'),
]

for (protocol_type, protocol_field) in multiprotocols:
    if spreadsheets.get(protocol_type) is not None:
        spreadsheets[protocol_type] = spreadsheets[protocol_type].fillna('')
        proto_df, proto_df_columns = split_multiprotocols(big_table, protocol_field)
        for proto_column in proto_df_columns:
            protocol_columns.append( (protocol_type, proto_column) )

        big_table = big_table.merge(proto_df, left_index=True, right_index=True)

# Saving the Big Table
big_table.to_csv(f"{work_dir}/big_table.csv", index=False, sep=";")


# Create protocol SCEA ids and map to HCA ids
# First, we prepare an ID minter for the protocols following SCEA MAGE-TAB standards.
protocol_id_counter = 0

def mint_proto_id():
    global protocol_id_counter
    protocol_id_counter += 1
    return f"P-{protocol_accession}-{protocol_id_counter}"

# Then, protocol map is created: a dict containing types of protocols, and inside each, a map from HCA ids to SCEA ids.
protocol_map = {x: {} for x in protocol_order}

for proto_type in protocol_order:
    for (ptype, proto_column) in protocol_columns:
        if ptype == proto_type:
            new_protos = pd.unique(big_table[proto_column]).tolist()
            protocol_map[proto_type].update({proto: {
                'id': mint_proto_id()
            } for proto in new_protos if proto is not None})

# Some more fields will be needed, like the description and the hardware used in some protocols, so here's a function
# to extract info from the protocols spreadsheets.
def extract_protocol_info(column_to_extract, to_key, for_protocols = protocol_order):
    for proto_type, proto_list in protocol_map.items():
        if proto_type in for_protocols:
            for proto_name, proto in proto_list.items():
                extracted_data = spreadsheets[proto_type].loc[spreadsheets[proto_type][f'{proto_type}.protocol_core.protocol_id'] == proto_name][f'{proto_type}.{column_to_extract}'].tolist()

                if len(extracted_data):
                    proto[to_key] = extracted_data[0]
                else:
                    proto[to_key] = ''

# Using that function, we get the description for all protocol types, and the hardware for sequencing protocols into
# the map.
extract_protocol_info(f"protocol_core.protocol_description", "description")
extract_protocol_info(f"instrument_manufacturer_model.ontology_label", "hardware", ["sequencing_protocol"])

# Creating the MAGE-TAB
# IDF File
# Python does not allow backslashes in f-strings, so we assign `\t` to `tab` and use that instead of a literal.
tab = "\t"

# Getter function for fields in spreadsheets. Will sanitize newlines into spaces.
def g(sheet, col_name, func=lambda x: x):
    data = None

    try:
        data = tab.join(func(p) for p in list(spreadsheets[sheet][col_name].fillna(''))).replace('\n', ' ')
    except:
        pass

    return data

# Getting dates from the humancellatlas API, as they are not in the spreadsheet.
project_uuid = g("project", "project.uuid") if force_project_uuid is None else force_project_uuid
submission_date = fill_this_label
last_update_date = fill_this_label
geo_accessions = []

if project_uuid:
    project_url = f"https://api.ingest.data.humancellatlas.org/projects/search/findByUuid?uuid={project_uuid}"
    project_response = requests.get(project_url)

    if project_response.status_code == 200:
        project_data = project_response.json()

        submission_date = dateutil.parser.isoparse(project_data['submissionDate']).strftime("%Y-%m-%d")
        last_update_date = dateutil.parser.isoparse(project_data['updateDate']).strftime("%Y-%m-%d")

        geo_accessions = project_data['content'].get('geo_series_accessions', [])

idf_file_contents = f"""MAGE-TAB Version\t1.1
Investigation Title\t{g("project", "project.project_core.project_title")}
Comment[Submitted Name]\t{g("project", "project.project_core.project_short_name")}
Experiment Description\t{g("project", "project.project_core.project_description")}
Public Release Date\t{last_update_date}
Person First Name\t{g("project_contributors", "project.contributors.name", lambda x: x.split(',')[0])}
Person Last Name\t{g("project_contributors", "project.contributors.name", lambda x: x.split(',')[2])}
Person Mid Initials\t{g("project_contributors", "project.contributors.name", lambda x: x.split(',')[1])}
Person Email\t{g("project_contributors", "project.contributors.email")}
Person Affiliation\t{g("project_contributors", "project.contributors.institution")}
Person Address\t{g("project_contributors", "project.contributors.address")}
Person Roles\t{g("project_contributors", "project.contributors.project_role.text")}
Protocol Type\t{tab.join([protocol_type_map[pt] for pt, pd in protocol_map.items() for pn, p in pd.items()])}
Protocol Name\t{tab.join([p['id'] for pt, pd in protocol_map.items() for pn, p in pd.items()])}
Protocol Description\t{tab.join([p['description'] for pt, pd in protocol_map.items() for pn, p in pd.items()])}
Protocol Hardware\t{tab.join([p.get('hardware', '') for pt, pd in protocol_map.items() for pn, p in pd.items()])}
Term Source Name\tEFO\tArrayExpress
Term Source File\thttp://www.ebi.ac.uk/efo/efo.owl\thttp://www.ebi.ac.uk/arrayexpress/
Comment[AEExperimentType]\tRNA-seq of coding RNA from single cells
Experimental Factor Name\t{fill_this_label}
Experimental Factor Type\t{fill_this_label}
Comment[EAAdditionalAttributes]\t{fill_this_label}
Comment[EACurator]\t{tab.join(curators)}
Comment[EAExpectedClusters]\t
Comment[ExpressionAtlasAccession]\t{accession}
Comment[HCALastUpdateDate]\t{last_update_date}
Comment[SecondaryAccession]\t{project_uuid}\t{tab.join(geo_accessions)}
Comment[EAExperimentType]\t{fill_this_label}
SDRF File\t{sdrf_file_name}
"""

with open(f"{idf_file_name}", "w") as idf_file:
    idf_file.write(idf_file_contents)

with open(f"./{work_dir}/protocol_map.json", "w") as protocol_map_file:
    json.dump(protocol_map, protocol_map_file, indent=2)