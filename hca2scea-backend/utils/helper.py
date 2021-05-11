import re

# Convert sheet names to snake case.
def convert_to_snakecase(label):
    return re.sub(r'(\s-\s)|\s', '_', label).lower()

# Helpers to convert lists in HCA spreadsheets (items are separated with two pipes `||`)
# to python lists.
def splitlist(list_):
    split_data = []
    try:
        if list_ != "nan":
            split_data = list_.split('||')
    except:
        pass
    return split_data
