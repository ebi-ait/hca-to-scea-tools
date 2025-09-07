import argparse
import os
import requests as rq
from xml.etree import ElementTree
import multiprocessing
from contextlib import contextmanager
import pandas as pd

@contextmanager
def poolcontext(*args, **kwargs):
    pool = multiprocessing.Pool(*args, **kwargs)
    yield pool
    pool.terminate()

def parse_xml(xml_content):
    for experiment_package in xml_content.findall('EXPERIMENT_PACKAGE'):
        yield experiment_package

def filter_paths(sdrf, paths):
    runs = list(sdrf['Comment[ENA_RUN]'])
    read1_files, read2_files = [], []
    index1_files, index2_files = [], []
    read1_paths, read2_paths = [], []
    index1_paths, index2_paths = [], []
    sra_paths, sra_read1_files, sra_read2_files = [], [], []
    for run in runs:
        if paths[run]['filetype'] == 'fastq file':
            read1_files.append(paths[run]['filename_read1'])
            read1_paths.append(paths[run]['filepath_read1'])
            read2_files.append(paths[run]['filename_read2'])
            read2_paths.append(paths[run]['filepath_read2'])
            index1_files.append(paths[run].get('filename_index1', ''))
            index1_paths.append(paths[run].get('filepath_index1', ''))
            index2_files.append(paths[run].get('filename_index2', ''))
            index2_paths.append(paths[run].get('filepath_index2', ''))
        elif paths[run]['filetype'] == 'SRA file':
            sra_paths.append(paths[run]['filepath'])
            sra_read1_files.append(f"{run}_1.fastq.gz")
            sra_read2_files.append(f"{run}_2.fastq.gz")
        else:
            continue
    if read1_files:
        sdrf['Comment[read1 file]'] = read1_files
        sdrf['Comment[read1 FASTQ_URI]'] = read1_paths
        sdrf['Comment[read2 file]'] = read2_files
        sdrf['Comment[read2 FASTQ_URI]'] = read2_paths
        sdrf['Comment[index1 file]'] = index1_files if index1_files else ['']*len(read1_files)
        sdrf['Comment[index1 FASTQ_URI]'] = index1_paths if index1_paths else ['']*len(read1_files)
        sdrf['Comment[SRA_URI]'] = '' * len(read1_files)
    elif sra_paths:
        sdrf['Comment[SRA_URI]'] = sra_paths
        sdrf['Comment[read1 file]'] = sra_read1_files
        sdrf['Comment[read2 file]'] = sra_read2_files
        sdrf['Comment[index1 file]'] = ['']*len(sra_read1_files)
        sdrf['Comment[read1 FASTQ_URI]'] = ['']*len(sra_read1_files)
        sdrf['Comment[read2 FASTQ_URI]'] = ['']*len(sra_read1_files)
        sdrf['Comment[index1 FASTQ_URI]'] = ['']*len(sra_read1_files)

    sdrf.drop_duplicates(keep=False, inplace=True)
    return sdrf

def sort_sra(paths):
    paths_new = paths
    for accession in paths.keys():
        sra_path = paths[accession]['files'][0]
        paths_new[accession]['filepath'] = sra_path
        paths_new[accession]['filetype'] = 'SRA file'
    return paths_new

def sort_fastq(paths):
    invalid_fastq = 'False'
    paths_new = paths
    sub_suffix_dict = {'_R1': 'read1', '_R2': 'read2', '_R3': 'index1', '_R4': 'index2', '_I1': 'index1', '_I2': 'index2'}
    gen_suffix_dict = {'_1': 'read1', '_2': 'read2', '_3': 'index1', '_4': 'index2'}
    for accession, path in paths.items():
        fastq = path['files']
        for file in fastq:
            if any(suffix in file for suffix in ['_R1', '_R2', '_R3', '_R4', '_I1', '_I2']):
                for suffix, read_type in sub_suffix_dict.items():
                    if suffix in file:
                        paths_new[accession][f'filename_{read_type}'] = os.path.basename(file)
                        paths_new[accession][f'filepath_{read_type}'] = file
            elif any(suffix in file for suffix in ['_1', '_2', '_3', '_4']) and '_R' not in file:
                for suffix, read_type in gen_suffix_dict.items():
                    if suffix in file:
                        paths_new[accession][f'filename_{read_type}'] = os.path.basename(file)
                        paths_new[accession][f'filepath_{read_type}'] = file
        paths_new[accession]['filetype'] = 'fastq file'
        if 'filename_read1' not in paths_new[accession].keys() or 'filename_read2' not in paths_new[accession].keys():
            invalid_fastq = 'True'
    if invalid_fastq == 'True':
        return {}
    else:
        return paths_new

def pool_retrieve_xml_from_sra(run_lists):
    try:
        result_list = []
        with poolcontext(processes=1) as pool:
            result_list.append(pool.map(get_sra_path_from_sra, run_lists))
    except KeyboardInterrupt:
        print("Process has been interrupted.")
        pool.terminate()
    return result_list

def run_accessions_to_parts(run_accessions):
    for i in range(0, len(run_accessions), 100):
        yield run_accessions[i:i + 100]

def retrieve_xml_from_sra(run_accessions):
    url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch/fcgi?db=sra&id={",".join(run_accessions)}'
    srr_metadata_url = rq.get(url)
    paths_sra = {}
    for accession in run_accessions:
        paths_sra[accession] = {}
        paths_sra[accession]['files'] = []
    try:
        tree = ElementTree.fromstring(srr_metadata_url.content)
        for experiment_package in tree.findall('EXPERIMENT_PACKAGE'):
            for run in experiment_package.find('RUN_SET'):
                attributes = run.find('SRAFiles')
                for sra_file in attributes:
                    sra_status = sra_file.attrib['sratoolkit']
                    if sra_status in ['1', 1]:
                        file_name = sra_file.attrib['filename']
                        if 'SRR' in file_name:
                            accession = file_name
                            file_path = sra_file.attrib['url']
                            paths_sra[accession]['files'].append(file_path)
                        else:
                             continue
    except:
        return {}
    return paths_sra

def get_sra_path_from_sra(run_accessions):
    run_accessions = [x for x in run_accessions if x]
    if len(run_accessions) > 100:
        run_lists = list(run_accessions_to_parts(run_accessions))
        result_list = pool_retrieve_xml_from_sra(run_lists)
        paths_sra = result_list
    else:
        paths_sra = retrieve_xml_from_sra(run_accessions)
    return paths_sra

def get_sra_path_from_ena(study_accession, run_accessions):
    paths_sra = {}
    try:
        request_url = f'http://www.ebi.ac.uk/ena/portal/api/filereport?accession={study_accession}&result=read_run&fields=run_accession,sra_ftp'
        sra_results = pd.read_csv(request_url, delimiter='\t')
        if sra_results.shape[0] == 0:
            return {}
        for i, accession in enumerate(list(sra_results['run_accession'])):
            if accession in run_accessions:
                paths_sra[accession] = {'files': []}
                file_path = str(list(sra_results['sra_ftp'])[i])
                file_path = "ftp://" + file_path
                paths_sra[accession]['files'].append(file_path)
    except:
        return {}
    return {acc: paths_sra[acc] for acc in run_accessions if acc in paths_sra}

def get_fastq_path_from_ena(study_accession, run_accessions):
    paths_fastq = {}
    try:
        request_url = f'http://www.ebi.ac.uk/ena/portal/api/filereport?accession={study_accession}&result=read_run&fields=run_accession,fastq_ftp'
        fastq_results = pd.read_csv(request_url, delimiter='\t')
        if fastq_results.shape[0] > 0:
            for i, row in fastq_results.iterrows():
                accession = row['run_accession']
                if accession not in run_accessions:
                    paths_fastq = {}
                    continue
                paths_fastq[accession] = {'files': []}
                if ';' in row['fastq_ftp']:
                    # The fastq file paths are split by ";" when retrieved using the above ENA url. If there is no ';' separater,
                    # this means that the number of available fastq files is <= 1. 2 is the minimum number required. If only 1
                    # fastq file is available then an empty dictionary is returned.
                    file_list = row['fastq_ftp'].split(';')
                    for file_path in file_list:
                        paths_fastq[accession]['files'].append(f"ftp://{file_path}")
                else:
                    continue
    except:
        return {}
    return {acc: paths_fastq[acc] for acc in run_accessions if acc in paths_fastq}
