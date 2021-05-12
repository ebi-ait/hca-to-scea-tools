import pandas as pd
from itertools import chain

from utils import helper

# Order of protocols.
protocol_order = [
    'collection_protocol',
    'dissociation_protocol',
    'enrichment_protocol',
    'library_preparation_protocol',
    'sequencing_protocol',
]

# Columns where protocols are stored in the spreadsheet.
#protocol_columns = {
#    'collection_protocol': ["collection_protocol.protocol_core.protocol_id"],
#    'library_preparation_protocol': ["library_preparation_protocol.protocol_core.protocol_id"],
#    'sequencing_protocol': ["sequencing_protocol.protocol_core.protocol_id"],
#}
protocol_columns = {}

multiprotocols = {
    'dissociation_protocol': "dissociation_protocol.protocol_core.protocol_id",
    'enrichment_protocol': "enrichment_protocol.protocol_core.protocol_id",
    'collection_protocol': "collection_protocol.protocol_core.protocol_id",
    'library_preparation_protocol': "library_preparation_protocol.protocol_core.protocol_id",
    'sequencing_protocol': "sequencing_protocol.protocol_core.protocol_id"
}

protocol_type_map = {
    'collection_protocol': "sample collection protocol",
    'dissociation_protocol': "enrichment protocol",
    '??????????????????????': "nucleic acid extraction protocol",
    'enrichment_protocol': "enrichment protocol",
    'library_preparation_protocol': "nucleic acid library construction protocol",
    'sequencing_protocol': "nucleic acid sequencing protocol",
}

def split_multiprotocols(df, proto_column):
    df = df.loc[:, ~df.columns.duplicated()]
    proto_series = df[proto_column].apply(helper.splitlist)
    proto_df = pd.DataFrame(proto_series.values.tolist())
    proto_df_columns = [f'{proto_column}_{y}' for y in range(len(proto_df.columns))]
    proto_df.columns = proto_df_columns
    proto_df[f'{proto_column}_count'] = proto_series.str.len()
    proto_df[f'{proto_column}_list'] = proto_series
    return (proto_df, proto_df_columns)

# Maps a HCA protocol name to a SCEA ID.
def map_proto_to_id(protocol_name, protocol_map):
    for proto_type in protocol_map.values():
        for proto in proto_type.values():
            if protocol_name in proto['hca_ids']:
                return proto.get('scea_id')
    return ''

# Extracts the protocols descriptions from tabs_dict and adds them to the protocol_map alongside
# the appropriate protocol id
def extract_protocol_description(
    protocol_map,
    tabs_dict,
    column_to_extract,
    to_key,
    for_protocols = protocol_order):
    for proto_type, proto_list in protocol_map.items():
        if proto_type in for_protocols:
            for proto_name, proto in proto_list.items():
                extracted_data = tabs_dict[proto_type].loc[tabs_dict[proto_type][f'{proto_type}.protocol_core.protocol_id'] == proto_name][f'{proto_type}.{column_to_extract}'].tolist()
                if len(extracted_data):
                    proto[to_key] = extracted_data[0]
                else:
                    proto[to_key] = ''

def get_proto_type_columns(merged_tabs, key):
    proto_type_columns = [column for column in merged_tabs.columns if key in column and 'count' not in column and 'list' not in column]
    if len(proto_type_columns) > 1:
        proto_type_columns.remove(key)
    return proto_type_columns

def get_proto_type_values(merged_tabs, key, proto_type_columns):
    proto_type_values = list(set(list(chain.from_iterable([list(merged_tabs[column]) for column in proto_type_columns]))))
    if key in proto_type_values:
        proto_type_values.remove(key)
    proto_type_values = [value for value in proto_type_values if isinstance(value, str)]
    proto_type_values_numbered = [value for value in proto_type_values if helper.has_numbers(value)]
    proto_type_values_numbered.sort(key=helper.natural_keys)
    proto_type_values_not_numbered = [value for value in proto_type_values if not helper.has_numbers(value)]
    proto_type_values = proto_type_values_numbered + proto_type_values_not_numbered
    return proto_type_values
