import pandas as pd
import requests as rq
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
    next_echad_accession = int(maxi) + 1
    return next_echad_accession

def get_next_accession():
    tracking_sheet = get_tracker_google_sheet()
    accessions = list(tracking_sheet['data_accession']) + list(tracking_sheet['scea_accession'])
    accessions_uniq = get_unique_accessions(accessions)
    echad_accessions = get_echad_accessions(accessions_uniq)
    accession_number = get_next_echad_accession(echad_accessions)
    return accession_number

def get_accessions_for_project(tracking_sheet: pd.DataFrame,identifier: str) -> []:
    '''
    Get the list of project accessions associated with a particular project from the tracker google sheet,
    the ingest project uuid as input. The accessions can be of multiple types.
    '''
    try:
        idx = tracking_sheet.index[tracking_sheet['ingest_project_uuid'] == identifier].tolist()[0]
    except:
        idx = None
    if idx:
        accession_list = list(tracking_sheet['data_accession'])[idx]
        return accession_list
    else:
        return None