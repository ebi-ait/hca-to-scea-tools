import re

def get_list_from_dict(dict, tab, key):
    return list(dict[tab][key].fillna('').replace(r'[\n\r]', ' ', regex=True))

def get_tab_separated_list_from_dict(dict, tab, key, func=lambda x: x):
    return '\t'.join([func(p) for p in get_list_from_dict(dict, tab, key)])

def get_first_letter(str):
    return str[0] if len(str) else ''

def replace_dash_with_to(input_list):
    updated_input_list = []
    for string_value in input_list:
        string_value = str(string_value)
        if ' - ' in string_value:
            string_value = string_value.replace('-', 'to')
        elif '-' in string_value and ' ' not in string_value:
            string_value = string_value.replace('-', ' to ')
        else:
            string_value = string_value
        updated_input_list.append(string_value)
    return updated_input_list

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
