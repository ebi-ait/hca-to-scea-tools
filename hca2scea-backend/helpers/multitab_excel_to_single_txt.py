from pathlib import Path
import numpy as np
import pandas as pd
import sys

from helpers import utils
from helpers import get_protocol_map
from helpers import cell_lines

def clean_dictionary(xlsx_dict):

    for filename in xlsx_dict.keys():
        xlsx_df = xlsx_dict[filename]
        xlsx_df_clean = xlsx_df.replace('', np.nan).dropna(how="all")
        xlsx_df_clean = xlsx_df_clean.loc[:, ~xlsx_df_clean.columns.str.contains('^Unnamed')]
        xlsx_dict[filename] = xlsx_df_clean

    '''Remove NAs in protocol dataframes.'''
    for protocol_type in get_protocol_map.map_of_hca_protocol_type_id_keys.keys():
        xlsx_dict[protocol_type] = xlsx_dict[protocol_type].fillna('')

    return xlsx_dict

def multitab_excel_to_dict(work_dir, excel_file):

    '''Each tab in the multitab excel_file is saved as a
    pandas dataframe. The set of dataframes are stored in
    a dictionary.
    '''

    xlsx = pd.ExcelFile(excel_file, engine='openpyxl')

    xlsx_dict = {}

    for sheet in xlsx.sheet_names:
        path = Path(work_dir)
        path.mkdir(parents=True, exist_ok=True)
        filename = f"{utils.convert_to_snakecase(sheet)}"
        xlsx_df = pd.read_excel(
            excel_file,
            sheet_name=sheet,
            header=0,
            skiprows=[0,1,2,4],
            engine='openpyxl')
        xlsx_dict[filename] = xlsx_df

    xlsx_dict_clean = clean_dictionary(xlsx_dict)

    return xlsx_dict_clean

def merge_dataframes(xlsx_dict: {}) -> pd.DataFrame():

    """Merge the sequence file df with the cell suspension df via the linked
     cell suspension ids."""

    '''process.insdc_experiment.insdc_experiment_accession' is present in multiple tabs. Save the cell_suspension experiment accessions with a unique name.'''
    xlsx_dict['cell_suspension']["cell_suspension.insdc_experiment.insdc_experiment_accession"] = list(xlsx_dict['cell_suspension']['process.insdc_experiment.insdc_experiment_accession'])

    merged_df = xlsx_dict['cell_suspension'].merge(
        xlsx_dict['sequence_file'],
        how="outer",
        on="cell_suspension.biomaterial_core.biomaterial_id"
    )

    ''' Get the experimental design '''
    experimental_design = utils.get_experimental_design(xlsx_dict)

    ''' Check if samples are pooled '''
    pooled_samples = utils.check_for_pooled_samples(xlsx_dict)
    if pooled_samples:
        print("The hca-to-scea tool does not support pooled donors or pooled samples."
              "The dataset should be curated manually.")
        sys.exit()

    if experimental_design != "standard":

        """If a cell_suspension id is derived from a cell_line id or an organoid id, get the specimen id."""
        merged_df = cell_lines.merge_cell_lines(xlsx_dict, merged_df, experimental_design)

    else:

        merged_df = xlsx_dict['specimen_from_organism'].merge(
            merged_df,
            how="outer",
            on="specimen_from_organism.biomaterial_core.biomaterial_id"
        )

    """Merge the merged_df with the donor_organism df via the linked
     donor_organism ids."""
    merged_df = xlsx_dict['donor_organism'].merge(
        merged_df,
        how="outer",
        on="donor_organism.biomaterial_core.biomaterial_id"
    )

    """Merge the merged_df with the library_preperation_protocol df via the linked
     library_preparation_protocol ids."""
    merged_df = xlsx_dict['library_preparation_protocol'].merge(
        merged_df,
        how="outer",
        on="library_preparation_protocol.protocol_core.protocol_id"
    )

    """Merge the merged_df with the sequencing_protocol df via the linked
     sequencing_protocol ids."""
    merged_df = xlsx_dict['sequencing_protocol'].merge(
        merged_df,
        how="outer",
        on="sequencing_protocol.protocol_core.protocol_id"
    )

    return merged_df


def merge_rows_by_read_pair(merged_df):

    merged_df_read1 = merged_df.loc[merged_df['sequence_file.read_index'] == 'read1']
    merged_df_read2 = merged_df.loc[merged_df['sequence_file.read_index'] == 'read2']

    merged_df_read2_short = merged_df_read2[[
        'cell_suspension.biomaterial_core.biomaterial_id',
        'sequence_file.file_core.file_name',
        'sequence_file.read_length',
        'sequence_file.lane_index',
    ]]

    merged_df_joined = merged_df_read1.merge(
        merged_df_read2_short,
        on=['cell_suspension.biomaterial_core.biomaterial_id', 'sequence_file.lane_index'],
        suffixes=("_read1", "_read2")
    )

    return merged_df_joined


def merge_index_reads(merged_df, merged_df_by_reads):

    merged_df = merged_df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    merged_df_index1 = merged_df.loc[merged_df['sequence_file.read_index'] == 'index1']

    merged_df_index1_short = merged_df_index1[[
        'cell_suspension.biomaterial_core.biomaterial_id',
        'sequence_file.file_core.file_name',
        'sequence_file.read_length',
        'sequence_file.lane_index',
    ]]

    merged_df_index1_short.columns = [f"{x}_index1" for x in merged_df_index1_short.columns]

    merged_df_by_index = merged_df_by_reads.merge(
            merged_df_index1_short,
            left_on=['cell_suspension.biomaterial_core.biomaterial_id', 'sequence_file.lane_index'],
            right_on=["cell_suspension.biomaterial_core.biomaterial_id_index1", 'sequence_file.lane_index_index1'],
        )

    return merged_df_by_index


def reorder_columns(df):

    df.reset_index(inplace=True)
    df = df.rename(
        columns={'sequence_file.file_core.file_name': 'sequence_file.file_core.file_name_read1'})
    df_sorted = df.reindex(sorted(df.columns), axis=1)
    df_sorted = df_sorted.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    reordered_df = df_sorted
    reordered_df['donor_organism.organism_age'] = df['donor_organism.organism_age']

    return reordered_df


def clean_df(df):

    '''Remove duplicate columns.'''
    df = df[[x for x in df.columns if x not in df.columns[df.columns.duplicated()]]]

    '''Reorder columns by column names.'''
    df_clean = reorder_columns(df)

    return df_clean


def create_new_protocol_columns(df, xlsx_dict):

    '''This extracts the lists from protocol types which can have more than one instance and creates extra columns in the
    df for each of the items.'''
    for (protocol_type, protocol_field) in get_protocol_map.multiprotocols.items():
        if xlsx_dict.get(protocol_type) is not None:
            xlsx_dict[protocol_type] = xlsx_dict[protocol_type].fillna('')
            proto_df, proto_df_columns = get_protocol_map.split_multiprotocols(df, protocol_field)
            for proto_column in proto_df_columns:
                if get_protocol_map.map_of_hca_protocol_type_id_keys.get(protocol_type) == None:
                    get_protocol_map.map_of_hca_protocol_type_id_keys[protocol_type] = []
                get_protocol_map.map_of_hca_protocol_type_id_keys[protocol_type].append(proto_column)

            df = df.merge(proto_df, left_index=True, right_index=True)

    return df