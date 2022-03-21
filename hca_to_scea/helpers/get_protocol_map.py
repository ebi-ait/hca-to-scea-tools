import pandas as pd

'''Map of HCA protocol type names to SCEA protocol type names.'''
protocol_type_map = {
    'collection_protocol': "sample collection protocol",
    'dissociation_protocol': "enrichment protocol",
    '??????????????????????': "nucleic acid extraction protocol",
    'enrichment_protocol': "enrichment protocol",
    "differentiation_protocol": "growth protocol",
    'library_preparation_protocol': "nucleic acid library construction protocol",
    'sequencing_protocol': "nucleic acid sequencing protocol",
}

'''Order of SCEA protocol type names by experimental stage (SCEA requirement).'''
ordered_hca_protocol_types = [
    'collection_protocol',
    'dissociation_protocol',
    'enrichment_protocol',
    'differentiation_protocol',
    'library_preparation_protocol',
    'sequencing_protocol',
]

'''HCA columns names for HCA protocol type ids.'''
map_of_hca_protocol_type_id_keys = {
    'collection_protocol': ["collection_protocol.protocol_core.protocol_id"],
    'library_preparation_protocol': ["library_preparation_protocol.protocol_core.protocol_id"],
    'sequencing_protocol': ["sequencing_protocol.protocol_core.protocol_id"]
}

'''There can be multiple dissociation protocols and/or enrichment protocols
performed on a single specimen. This dict stores such protocol types.'''
multiprotocols = {
    'dissociation_protocol': "dissociation_protocol.protocol_core.protocol_id",
    'enrichment_protocol': "enrichment_protocol.protocol_core.protocol_id",
    'differentiation_protocol': "differentiation_protocol.protocol_core.protocol_id"
}

'''There can be multiple dissociation protocols and/or enrichment protocols
performed on a single specimen. The following 2 functions convert a lists of protocols
from an HCA spreadsheet, separated by '||', to a standard python list.'''
def splitlist(list_):

    split_data = []
    try:
        if list_ != "nan" and list_ != "":
            split_data = list_.split('||')
            split_data = sorted(split_data)
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

'''Given a list of unique protocol type ids, get the corresponding protocol type id
in SCEA's protocol accession format.'''
def get_scea_protocol_id(dataset_protocol_map, hca_protocol_type, hca_protocol_type_ids,
                         scea_protocol_accession, protocol_id_counter):

    for hca_protocol_type_id in hca_protocol_type_ids:
        if hca_protocol_type_id is not None:
            protocol_id_counter += 1
            scea_protocol_type_id = f"P-{scea_protocol_accession}-{protocol_id_counter}"
            dataset_protocol_map[hca_protocol_type].update({hca_protocol_type_id:
                                                                {'scea_id': scea_protocol_type_id,
                                                                 'hca_ids': [hca_protocol_type_id]}})

    return dataset_protocol_map, protocol_id_counter


'''For HCA protocol type in the ordered list of HCA protocols, get the list of unique
protocol type ids given the hca protocol type id key (column) for the HCA protocol type.'''
def get_unique_protocol_ids(df, map_of_hca_protocol_type_id_keys, hca_protocol_type):

    for (hca_ptype, hca_protocol_type_id_keys) in map_of_hca_protocol_type_id_keys.items():
        if hca_ptype == hca_protocol_type:
            hca_protocol_type_ids = []
            for hca_protocol_type_id_key in hca_protocol_type_id_keys:
                hca_protocol_type_ids = hca_protocol_type_ids + pd.unique(df[hca_protocol_type_id_key]).tolist()

    return hca_protocol_type_ids

'''Create a dataset protocol map (dictionary), containing types of HCA protocols and inside each,
 a map from HCA ids to SCEA ids.'''
def get_dataset_protocol_map(df, ordered_hca_protocol_types, map_of_hca_protocol_type_id_keys, scea_protocol_accession_prefix):

    '''First, we prepare an ID minter for the protocols following SCEA MAGE-TAB standards.'''
    protocol_id_counter = 0

    '''Create empty dictionary to store the HCA protocol ids mapped to the SCEA protocol ids.'''
    dataset_protocol_map = {x: {} for x in ordered_hca_protocol_types}

    for hca_protocol_type in ordered_hca_protocol_types:

        if hca_protocol_type in map_of_hca_protocol_type_id_keys.keys():

            '''For HCA protocol type in the ordered list of HCA protocols, get the list of unique
            protocol type ids given the hca protocol type id key (column) for the HCA protocol type.'''
            hca_protocol_type_ids = get_unique_protocol_ids(df, map_of_hca_protocol_type_id_keys, hca_protocol_type)

            '''Given a list of unique protocol type ids, get the corresponding protocol type id
            in SCEA's protocol accession format and update the dataset_protocol_map.'''
            dataset_protocol_map, protocol_id_counter = get_scea_protocol_id(dataset_protocol_map, hca_protocol_type, hca_protocol_type_ids, scea_protocol_accession_prefix, protocol_id_counter)

    return dataset_protocol_map

'''Extracts hca protocol metadata from the hca protocol dataframes in xlsx_dict.'''
def extract_protocol_metadata(
    dataset_protocol_map,
    xlsx_dict,
    column_to_extract,
    new_key,
    hca_protocol_types
):
    for hca_protocol_type, hca_protocol_type_dict in dataset_protocol_map.items():
        if hca_protocol_type in hca_protocol_types:
            for hca_protocol_type_id, hca_protocol_type_id_dict in hca_protocol_type_dict.items():
                extracted_data = xlsx_dict[hca_protocol_type].loc[xlsx_dict[hca_protocol_type][f'{hca_protocol_type}.protocol_core.protocol_id'] == hca_protocol_type_id][f'{hca_protocol_type}.{column_to_extract}'].tolist()
                if len(extracted_data):
                    hca_protocol_type_id_dict[new_key] = extracted_data[0]
                else:
                    hca_protocol_type_id_dict[new_key] = ''

# Get protocol types from protocol map.
def get_idf_file_protocol_fields(protocol_map):

    proto_types = [protocol_type_map[protocol_type] for (protocol_type, value) in protocol_map.items() for repeats in range(len(value.keys()))]
    proto_names = [protocol['scea_id'] for (protocol_type, protocols) in protocol_map.items() for (protocol_name, protocol) in protocols.items()]
    proto_descs = [protocol['description'] for (protocol_type, protocols) in protocol_map.items() for (protocol_name, protocol) in protocols.items()]
    proto_hware = [protocol.get('hardware', '') for (protocol_type, protocols) in protocol_map.items() for (protocol_name, protocol) in protocols.items()]

    return list(zip(proto_types, proto_names, proto_descs, proto_hware))

'''Maps a HCA protocol name to a SCEA ID.'''
def map_proto_to_id(protocol_name, protocol_map):
    for key,proto_type in protocol_map.items():
        for proto in proto_type.values():
            if protocol_name in proto['hca_ids']:
                return proto.get('scea_id')
    return ''

def prepare_protocol_map(xlsx_dict, df, args):

    scea_protocol_accession_prefix = f"HCAD{args.accession_number}"

    dataset_protocol_map = get_dataset_protocol_map(df,
                                                    ordered_hca_protocol_types,
                                                    map_of_hca_protocol_type_id_keys,
                                                    scea_protocol_accession_prefix)

    ''' Get the description text for all protocol types.'''
    extract_protocol_metadata(dataset_protocol_map, xlsx_dict,
                              f"protocol_core.protocol_description", "description",
                              ordered_hca_protocol_types)

    ''' Get the instrument type and hardware type for the sequencing protocol(s).'''
    extract_protocol_metadata(dataset_protocol_map, xlsx_dict,
                              f"instrument_manufacturer_model.ontology_label", "hardware",
                              ["sequencing_protocol"])

    return dataset_protocol_map