"""
Import required modules.
"""
import pandas as pd
import requests as rq
import xml.etree.ElementTree as xm
import re

import utils.sra_utils as sra_utils

"""
Define functions.
"""
def request_fastq_from_ENA(srp_accession: str) -> {}:
    """
    Function to retrieve fastq file paths from ENA given an SRA study accession. The request returns a
    dataframe with a list of run accessions and their associated fastq file paths. The multiple file paths for
    each run are stored in a single string. This string is then stored in a dictionary with the associated
    run accessions as keys.
    """
    fastq_map = {}
    try:
        request_url = f'http://www.ebi.ac.uk/ena/data/warehouse/filereport?accession={srp_accession}&result=read_run&fields=run_accession,fastq_ftp'
        fastq_results = pd.read_csv(request_url, delimiter='\t')
        for i in range(0,fastq_results.shape[0]):
            paths = list(fastq_results['fastq_ftp'])[i].split(';')
            if len(paths) <= 1:
                return None
            else:
                for j in range(0,len(paths)):
                    fastq_map[list(fastq_results['run_accession'])[i]].update({'url%s' % (str(j+1)): paths[j], 'type': 'fastq'})
                return fastq_map
    except:
        return None

def extract_reads_ENA(ftp_path: str) -> []:
    """
    Function to extract single fastq file names from a string containing multiple fastq file paths.
    """
    try:
        read_files = ftp_path.split(';')
    except:
        read_files = []
    return read_files

def get_file_names_from_SRA(experiment_package: object, fastq_map: {}) -> {}:
    """
    Gets fastq file names from an xml returned from SRA following a request with a list
    of run accessions.
    """
    run_set = experiment_package.find('RUN_SET')
    for run in run_set:
        try:
            accession = run.attrib['accession']
            run_attributes = run.find('SRAFiles')
            attributes = run_attributes.findall('SRAFile')
            for attribute in attributes:
                urls = [attribute.attrib['url']]
                alternatives = attribute.findall('Alternatives')
                for alternative in alternatives:
                    urls.append(alternative.attrib['url'])
                paths = [url for url in urls if 'fastq.gz' in url or 'bam' in url]
                if len(paths) >= 1:
                    url = paths[0]
                else:
                    url = urls[0]
                if accession in fastq_map.keys():
                    if url not in fastq_map[accession]['urls']:
                        fastq_map[accession]['urls'].append(url)
                else:
                    fastq_map[accession] = {'urls': [url]}
        except:
            continue
    return fastq_map

def get_fastq_from_SRA(srr_accessions: []) -> {}:
    """
    Function to parse the xml output following a request for run accession metadata to the NCBI SRA database.
    A list of SRA run accessions is given as input to the request. The fastq file paths are extracted from
    this xml and the file names are added to a dictionary with the associated run accessions as keys (fastq_map).
    """
    xml_content = sra_utils.SraUtils.request_fastq_from_SRA(srr_accessions)
    if not xml_content:
        fastq_map = None
    else:
        fastq_map = {}
        experiment_packages = sra_utils.SraUtils.parse_xml_SRA_runs(xml_content)
        for experiment_package in experiment_packages:
            try:
                fastq_map = get_file_names_from_SRA(experiment_package,fastq_map)
            except:
                continue
    return fastq_map

def get_lane_index(file: str) -> str:
    """
    Looks for a lane index inside a fastq file name and returns the lane index if found.
    """
    result = re.search('_L[0-9]{3}', file)
    return result

def get_file_index(file: str) -> str:
    """
    Looks for a read index inside a fastq file name (R1,R2,I1,etc.). Returns the read index if found.
    """
    if "_I1" in file or "_R3" in file or "_3" in file:
        ind = 'index1'
    elif "_R1" in file or "_1" in file:
        ind = 'read1'
    elif "_R2" in file or "_2" in file:
        ind = 'read2'
    elif "_I2" in file or "_R4" in file or "_4" in file:
        ind = 'index2'
    else:
         ind = ''
    return ind
