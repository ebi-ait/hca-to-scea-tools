#
## HCA-TO-SCEA helper functions and maps.
#

import glob
import re

from os.path import splitext, basename

import pandas as pd


# Protocol mapping.
protocol_type_map = {
    'collection_protocol': "sample collection protocol",
    'dissociation_protocol': "enrichment protocol",
    '??????????????????????': "nucleic acid extraction protocol",
    'enrichment_protocol': "enrichment protocol",
    'library_preparation_protocol': "nucleic acid library construction protocol",
    'sequencing_protocol': "nucleic acid sequencing protocol",
}

# Order of protocols.
protocol_order = [
    'collection_protocol',
    'dissociation_protocol',
    'enrichment_protocol',
    'library_preparation_protocol',
    'sequencing_protocol',
]

# Columns where protocols are stored in the spreadsheet.
protocol_columns = {
    'collection_protocol': ["collection_protocol.protocol_core.protocol_id"],
    'library_preparation_protocol': ["library_preparation_protocol.protocol_core.protocol_id"],
    'sequencing_protocol': ["sequencing_protocol.protocol_core.protocol_id"],
}

multiprotocols = {
    'dissociation_protocol': "dissociation_protocol.protocol_core.protocol_id",
    'enrichment_protocol': "enrichment_protocol.protocol_core.protocol_id",
}


# Convert sheet names to snake case.
def convert_to_snakecase(label):
    return re.sub(r'(\s-\s)|\s', '_', label).lower()


# Fetch all spreadsheet csv in a dir.
def get_all_spreadsheets(work_dir):
    file_names = glob.glob(f"{work_dir}/*.csv")
    file_names = [x for x in file_names if not 'big_table.csv' in x]

    spreadsheets = {}

    for file_name in file_names:
        spreadsheets[convert_to_snakecase(splitext(basename(file_name))[0])] = file_name

    for name, file_name in spreadsheets.items():
        newSheet = pd.read_csv(file_name, header=0, sep=";", skiprows=[0,1,2,4])
        newSheet = newSheet.applymap(str)
        newSheet = newSheet.applymap(lambda x: x.strip())
        spreadsheets[name] = newSheet.loc[:, ~newSheet.columns.str.contains('^Unnamed')]

    return spreadsheets


# Extract lists of protocols
# Helpers to convert lists in HCA spreadsheets (items are separated with two
# pipes `||`) to python lists.
def splitlist(list_):
    split_data = []

    try:
        if list_ != "nan":
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


# Extracts info from the protocols spreadsheets
def extract_protocol_info(
    protocol_map,
    spreadsheets,
    column_to_extract,
    to_key,
    for_protocols = protocol_order
):
    for proto_type, proto_list in protocol_map.items():
        if proto_type in for_protocols:
            for proto_name, proto in proto_list.items():
                extracted_data = spreadsheets[proto_type].loc[spreadsheets[proto_type][f'{proto_type}.protocol_core.protocol_id'] == proto_name][f'{proto_type}.{column_to_extract}'].tolist()

                if len(extracted_data):
                    proto[to_key] = extracted_data[0]
                else:
                    proto[to_key] = ''


# Get protocol types from protocol map.
def get_protocol_idf(protocol_map):
    proto_types = [protocol_type_map[protocol_type] for (protocol_type, value) in protocol_map.items() for repeats in range(len(value.keys()))]
    proto_names = [protocol['scea_id'] for (protocol_type, protocols) in protocol_map.items() for (protocol_name, protocol) in protocols.items()]
    proto_descs = [protocol['description'] for (protocol_type, protocols) in protocol_map.items() for (protocol_name, protocol) in protocols.items()]
    proto_hware = [protocol.get('hardware', '') for (protocol_type, protocols) in protocol_map.items() for (protocol_name, protocol) in protocols.items()]

    return list(zip(proto_types, proto_names, proto_descs, proto_hware))


# Maps a HCA protocol name to a SCEA ID.
def map_proto_to_id(protocol_name, protocol_map):
    for proto_type in protocol_map.values():
        for proto in proto_type.values():
            if protocol_name in proto_type:
                return proto.get('scea_id')
    return ''
