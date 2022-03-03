#
## HCA-TO-SCEA helper functions and maps.
#

import glob
import re
import sys

import requests as rq
from itertools import chain
import copy

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

def get_experimental_design(xlsx_dict: {}):

    if 'specimen_from_organism' in xlsx_dict.keys():
        if xlsx_dict['specimen_from_organism'].empty:
            specimen = False
        else:
            specimen = True
    else:
        specimen = Falseprotocol_type_map

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

def filter_biomaterials(xlsx_dict, xlsx_dict_tmp, library_protocol):

    xlsx_dict_tmp["sequence_file"] = xlsx_dict["sequence_file"].loc[
        xlsx_dict["sequence_file"]["library_preparation_protocol.protocol_core.protocol_id"] == library_protocol]
    cell_suspension_ids = xlsx_dict_tmp["sequence_file"]["cell_suspension.biomaterial_core.biomaterial_id"].values
    xlsx_dict_tmp["cell_suspension"] = xlsx_dict["cell_suspension"][
        xlsx_dict["cell_suspension"]["cell_suspension.biomaterial_core.biomaterial_id"].isin((cell_suspension_ids))]

    biomaterial_tabs = ["specimen_from_organism", "organoid", "cell_line"]
    for biomaterial_tab in biomaterial_tabs:
        if biomaterial_tab in xlsx_dict.keys():
            id_column = "{}.biomaterial_core.biomaterial_id".format(biomaterial_tab)
            if id_column in xlsx_dict[biomaterial_tab] and not xlsx_dict[biomaterial_tab].empty:
                specimen_ids = xlsx_dict_tmp["cell_suspension"][
                    "{}.biomaterial_core.biomaterial_id".format(biomaterial_tab)].values
                xlsx_dict_tmp[biomaterial_tab] = xlsx_dict[biomaterial_tab][
                    xlsx_dict[biomaterial_tab]["{}.biomaterial_core.biomaterial_id".format(biomaterial_tab)].isin(
                        (specimen_ids))]
                donor_ids_specimen = xlsx_dict_tmp[biomaterial_tab][
                    "donor_organism.biomaterial_core.biomaterial_id"].values
                xlsx_dict_tmp["donor_organism"] = xlsx_dict["donor_organism"][
                    xlsx_dict["donor_organism"]["donor_organism.biomaterial_core.biomaterial_id"].isin(
                        (donor_ids_specimen))]

    return xlsx_dict_tmp

def filter_protocols(xlsx_dict_tmp):

    biomaterial_tabs = ["specimen_from_organism", "organoid", "cell_line", "cell_suspension", "sequence_file"]
    protocol_tabs = ["collection_protocol","dissociation_protocol","enrichment_protocol","differentiation_protocol","library_preparation_protocol","sequencing_protocol"]

    for protocol_tab in protocol_tabs:
        if protocol_tab in xlsx_dict_tmp.keys():
            id_column = "{}.protocol_core.protocol_id".format(protocol_tab)
            protocol_ids = list(xlsx_dict_tmp[protocol_tab][id_column])
            protocol_id_list = []
            for biomaterial_tab in biomaterial_tabs:
                if biomaterial_tab in xlsx_dict_tmp.keys():
                    if id_column in xlsx_dict_tmp[biomaterial_tab].columns:
                        protocol_id_list.extend(list(set(list(xlsx_dict_tmp[biomaterial_tab][id_column]))))
            remove_protocols = [i for i in range(0,len(protocol_ids)) if protocol_ids[i] not in protocol_id_list]
            xlsx_dict_tmp[protocol_tab].drop(xlsx_dict_tmp[protocol_tab].index[remove_protocols])

    return xlsx_dict_tmp

def split_metadata_by_technology(xlsx_dict):

    library_protocols_uniq = list(set(list(xlsx_dict["library_preparation_protocol"]["library_preparation_protocol.protocol_core.protocol_id"])))

    if len(library_protocols_uniq) == 1:
        list_xlsx_dict = [xlsx_dict]

    else:

        list_xlsx_dict = []
        for i in range(0,len(library_protocols_uniq)):

            xlsx_dict_tmp = copy.deepcopy(xlsx_dict)
            library_protocol = library_protocols_uniq[i]

            xlsx_dict_tmp = filter_biomaterials(xlsx_dict,xlsx_dict_tmp,library_protocol)
            xlsx_dict_tmp2 = copy.deepcopy(xlsx_dict_tmp)
            xlsx_dict_tmp3 = filter_protocols(xlsx_dict_tmp2)

            list_xlsx_dict.append(xlsx_dict_tmp3)

    return list_xlsx_dict

def get_related_scea_accessions(args, accession, related_scea_accessions):

    if args.related_scea_accession:
        related_scea_accession = args.related_scea_accession
        related_scea_accession = accession.split("E-HCAD-")[0] + str(related_scea_accession)
    else:
        related_scea_accession = None
    if related_scea_accessions:
        related_scea_accessions = [str(accession.split("E-HCAD-")[0]) + str(related_scea_acc) for related_scea_acc in related_scea_accessions]
        if related_scea_accession:
            related_scea_accessions.extend(related_scea_accession)

    return related_scea_accessions

