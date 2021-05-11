import pandas as pd

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
protocol_columns = {
    'collection_protocol': ["collection_protocol.protocol_core.protocol_id"],
    'library_preparation_protocol': ["library_preparation_protocol.protocol_core.protocol_id"],
    'sequencing_protocol': ["sequencing_protocol.protocol_core.protocol_id"],
}

multiprotocols = {
    'dissociation_protocol': "dissociation_protocol.protocol_core.protocol_id",
    'enrichment_protocol': "enrichment_protocol.protocol_core.protocol_id",
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

# Extracts info from the protocols spreadsheets
def extract_protocol_info(
    protocol_map,
    spreadsheets,
    column_to_extract,
    to_key,
    for_protocols = protocol_order):
    for proto_type, proto_list in protocol_map.items():
        if proto_type in for_protocols:
            for proto_name, proto in proto_list.items():
                extracted_data = spreadsheets[proto_type].loc[spreadsheets[proto_type][f'{proto_type}.protocol_core.protocol_id'] == proto_name][f'{proto_type}.{column_to_extract}'].tolist()
                if len(extracted_data):
                    proto[to_key] = extracted_data[0]
                else:
                    proto[to_key] = ''