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

    if col_name == "project.publications.pmid":
        values = list(sheet_dict[sheet][col_name].fillna('').replace(r'[\n\r]', ' ', regex=True))[0]
        if isinstance(values,float):
            values = str(int(values))
        else:
            values = values
    else:
        values = list(sheet_dict[sheet][col_name].fillna('').replace(r'[\n\r]', ' ', regex=True))

    return values

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

def save_files(work_dir, idf_file_name, sdrf_file_name, idf_file_contents, sdrf_file_contents):

    print(f"saving {work_dir}/{idf_file_name}")
    with open(f"{work_dir}/{idf_file_name}", "w") as idf_file:
        idf_file.write(idf_file_contents)

    '''Write the new sdrf file to a file.'''
    if not sdrf_file_contents.empty:
        print(f"saving {work_dir}/{sdrf_file_name}")
        sdrf_file_contents.to_csv(f"{work_dir}/{sdrf_file_name}", sep="\t", index=False)

def save_files_zip(zip_file,work_dir,idf_file_contents,sdrf_file_contents,idf_file_name,sdrf_file_name):

    print(f"saving {work_dir}/{idf_file_name}")
    with open(f"{work_dir}/{idf_file_name}", "w") as idf_file:
        idf_file.write(idf_file_contents)
    zip_file.write(f"{work_dir}/{idf_file_name}")

    if not sdrf_file_contents.empty:
        print(f"saving {work_dir}/{sdrf_file_name}")
        sdrf_file_contents.to_csv(f"{work_dir}/{sdrf_file_name}", sep="\t", index=False)
        zip_file.write(f"{work_dir}/{sdrf_file_name}")



