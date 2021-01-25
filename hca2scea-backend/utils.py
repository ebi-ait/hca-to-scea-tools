import argparse
import requests as rq
import pandas as pd
from itertools import chain

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
    maxi = int(maxi) + 1
    next_echad_accession = 'E-HCAD-' + str(maxi)
    return next_echad_accession

def get_accessions_for_project(tracking_sheet: pd.DataFrame,identifier: str,identifier_type: str) -> []:
    '''
    Get the list of project accessions associated with a particular project from the tracker google sheet, using either
    the ingest project uuid or the project short name as input. The accessions can be of multiple types.
    '''
    idx = None
    if identifier_type == 'project_uuid':
        try:
            idx = tracking_sheet.index[tracking_sheet['ingest_project_uuid'] == identifier].tolist()[0]
        except:
            idx = None
    elif identifier_type == 'project_short_name':
        try:
            idx = tracking_sheet.index[tracking_sheet['project_short_name'] == identifier].tolist()[0]
        except:
            idx = None
    if idx:
        accession_list = list(tracking_sheet['data_accession'])[idx]
        return accession_list
    else:
        return None

def parse_arguments():
    '''
    Parse user-defined command-line arguments.
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", default=None, help="Provide an ingest project uuid or the project short name")
    parser.add_argument("-it", default='project_uuid', choices = ['project_uuid','project_short_name'],
                        help="Indicate whether the given identifier is an ingest project uuid or a project short name. Must be 1 of project_uuid or project_short_name")
    return parser.parse_args()

def main():

    args = parse_arguments()

    '''
    Parse tracker google sheet as pd.DataFrame.
    '''
    tracking_sheet = get_tracker_google_sheet()

    '''
    Get the list of unique E-HCAD accessions from the tracker sheet and identify what the next E-HCAD id should be according
    to the number ordered list.
    '''
    accessions = list(tracking_sheet['data_accession']) + list(tracking_sheet['scea_accession'])
    accessions_uniq = get_unique_accessions(accessions)
    echad_accessions = get_echad_accessions(accessions_uniq)
    next_echad_accession = get_next_echad_accession(echad_accessions)

    '''
    Get the list of secondary accessions for a project from the tracker sheet by querying either an ingest project uuid
    or the project short name as input.'''
    accessions = get_accessions_for_project(tracking_sheet, identifier=args.i, identifier_type=args.it)
    if accessions:
        accessions_uniq = get_unique_accessions([accessions])
        [accessions_uniq.remove(accession) for accession in accessions_uniq if 'HCAD' in accession.upper()]

if __name__ == '__main__':
    main()