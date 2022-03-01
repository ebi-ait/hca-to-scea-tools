#
## HCA-TO-SCEA helper functions and maps.
#

import glob
import re

import requests as rq
from itertools import chain

from os.path import splitext, basename

import pandas as pd

def convert_to_snakecase(label):
    return re.sub(r'(\s-\s)|\s', '_', label).lower()

def reformat_value(sheet_dict, sheet, col_name):
    return list(sheet_dict[sheet][col_name].fillna('').replace(r'[\n\r]', ' ', regex=True))

def get_tab_separated_list(sheet_dict, sheet, col_name, func=lambda x: x):
    tab = '\t'
    return tab.join([func(p) for p in reformat_value(sheet_dict, sheet, col_name)])

def get_first_letter(str):
    return str[0] if len(str) else ''

def get_tracker_google_sheet() -> pd.DataFrame:
    '''
    Parse the tracker google sheet where we store all our dataset tracking data. Return it as a pd.DataFrame.
    '''
    tracking_sheet = rq.get("https://docs.google.com/spreadsheets/d/e/2PACX-1vQ26K0ZYREykq2kR2HgA3xGol3PfFuwYu"
                            "qNBQCZgi4L7yqF2GZiNdXfQ19FtjxMvCk8IU6S_v6zih9z/pub?gid=0&single=true&output=tsv",
                            headers={'Cache-Control': 'no-cache'}).text.splitlines()
    tracking_sheet = [data.split("\t") for data in tracking_sheet]
    tracking_sheet = pd.DataFrame(tracking_sheet[1:], columns=tracking_sheet[0])
    return tracking_sheet

def get_unique_accessions(accessions: []) -> []:
    '''
    Get the list of unique project accessions from the google tracker sheet. This includes multiple accession types,
    and accounts for a list of >1 accession for some projects.
    '''
    accessions_uniq = []
    accessions_uniq.extend([accession for accession in accessions if ',' not in accession and ';' not in accession])
    accessions_uniq.extend(list(chain(*[accession.split(",") for accession in accessions if ',' in accession])))
    accessions_uniq.extend(list(chain(*[accession.split(";") for accession in accessions if ';' in accession])))
    return accessions_uniq

def get_echad_accessions(accessions_uniq: []) -> []:
    '''
    Get the list of unique E-HCAD accessions from the google tracker sheet, given the list of all unique accessions types.
    '''
    echad_accessions = list(set([accession.strip() for accession in accessions_uniq if 'E-HCAD' in accession]))
    return echad_accessions

def get_next_echad_accession(ehcad_accessions: []) -> str:
    '''
    Order the list of unique E-HCAD accessions found in the tracker google sheet and identify which E-HCAD accession id
    should be next.
    '''
    ehcad_accessions = [ehcad.upper().replace('-','') for ehcad in ehcad_accessions]
    ehcad_accessions = [ehcad.split("EHCAD")[1] for ehcad in ehcad_accessions]
    maxi = sorted(ehcad_accessions,key=float)[-1]
    next_echad_accession = int(maxi) + 1
    return next_echad_accession

def get_accessions_for_project(tracking_sheet: pd.DataFrame,identifier: str) -> []:
    '''
    Get the list of project accessions associated with a particular project from the tracker google sheet, using either
    the ingest project uuid or the project short name as input. The accessions can be of multiple types.
    '''
    idx = None
    try:
        idx = tracking_sheet.index[tracking_sheet['ingest_project_uuid'] == identifier].tolist()[0]
    except:
        idx = None
    if idx:
        accession_list = list(tracking_sheet['data_accession'])[idx]
        return accession_list
    else:
        return None

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
            if protocol_name in proto['hca_ids']:
                return proto.get('scea_id')
    return ''

def get_experimental_design(xlsx_dict: {}):

    if 'specimen_from_organism' in xlsx_dict.keys():
        if xlsx_dict['specimen_from_organism'].empty:
            specimen = False
        else:
            specimen = True
    else:
        specimen = False

    if 'cell_line' in xlsx_dict.keys():
        if xlsx_dict['cell_line'].empty:
            cell_line = False
        else:
            cell_line = True
    else:
        cell_line = False

    if 'organoid' in xlsx_dict.keys():
        if xlsx_dict['organoid'].empty:
            organoid = False
        else:
            organoid = True
    else:
        organoid = False

    if specimen:

        if cell_line and not organoid:
            experimental_design = "cell_line_only"
        elif not cell_line and organoid:
            experimental_design = "organoid_only"
        elif cell_line and organoid:
            experimental_design = "organoid"
        else:
            experimental_design = "standard"

    return experimental_design

def check_for_pooled_samples(xlsx_dict):

    df = xlsx_dict["specimen_from_organism"]
    specimen_ids = list(df['specimen_from_organism.biomaterial_core.biomaterial_id'])
    pooled_samples_specimen = [specimen_id for specimen_id in specimen_ids if "||" in specimen_id]

    pooled_samples_cell_line = []
    if "cell_line" in xlsx_dict.keys() and not xlsx_dict["cell_line"].empty:
        df = xlsx_dict["cell_line"]
        if 'cell_line.biomaterial_core.biomaterial_id' in df.columns:
            cell_line_ids = list(df['cell_line.biomaterial_core.biomaterial_id'])
            pooled_samples_cell_line = [cell_line_id for cell_line_id in cell_line_ids if "||" in cell_line_id]

    pooled_samples_organoid = []
    if "organoid" in xlsx_dict.keys() and not xlsx_dict["organoid"].empty:
        df = xlsx_dict["organoid"]
        if 'organoid.biomaterial_core.biomaterial_id' in df.columns:
            organoid_ids = list(df['organoid.biomaterial_core.biomaterial_id'])
            pooled_samples_organoid = [organoid_id for organoid_id in organoid_ids if "||" in organoid_id]

    df = xlsx_dict["donor_organism"]
    donor_ids = list(df['donor_organism.biomaterial_core.biomaterial_id'])
    pooled_samples_donor = [donor_id for donor_id in donor_ids if "||" in donor_id]

    if pooled_samples_specimen or pooled_samples_donor or pooled_samples_cell_line or pooled_samples_organoid:
        pooled_samples = True
    else:
        pooled_samples = False

    return pooled_samples