import re

def atoi(text):
    if text.isdigit():
        return int(text)
    else:
        return text

def natural_keys(text):
    return [ atoi(c) for c in re.split('(\d+)',text) ]

def has_numbers(input_string):
    return any(char.isdigit() for char in input_string)

# Convert sheet names to snake case.
def convert_to_snakecase(label):
    return re.sub(r'(\s-\s)|\s', '_', label).lower()

# Helper to convert lists in HCA spreadsheets (items are separated with two pipes `||`)
# to python lists.
def splitlist(list_):
    split_data = []
    try:
        if list_ != "nan":
            if '||' in list_:
                split_data = list_.split('||')
            else:
                split_data = [list_]
    except:
        pass
    return split_data
