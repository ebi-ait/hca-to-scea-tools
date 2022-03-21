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
    read1_files = []
    read2_files = []
    index1_files = []
    index2_files = []
    read1_paths = []
    read2_paths = []
    index1_paths = []
    index2_paths = []
    sra_paths = []
    sra_read1_files = []
    sra_read2_files = []
    for i in range(0, len(runs)):
        run = runs[i]
        if paths[run]['filetype'] == 'fastq file':
            read1_files.append(paths[run]['filename_read1'])
            read1_paths.append(paths[run]['filepath_read1'])
            read2_files.append(paths[run]['filename_read2'])
            read2_paths.append(paths[run]['filepath_read2'])
            if 'filename_index1' in paths[run].keys():
                index1_files.append(paths[run]['filename_index1'])
                index1_paths.append(paths[run]['filepath_index1'])
            else:
                index1_files.append('')
                index1_paths.append('')
            if 'filename_index2' in paths[run].keys():
                index2_files.append(paths[run]['filename_index2'])
                index2_paths.append(paths[run]['filepath_index2'])
            else:
                index2_files.append('')
                index2_paths.append('')
        elif paths[run]['filetype'] == 'SRA file':
            sra_paths.append(paths[run]['filepath'])
            file1 = run + "_1.fastq.gz"
            file2 = run + "_2.fastq.gz"
            sra_read1_files.append(file1)
            sra_read2_files.append(file2)
        else:
            continue
    if read1_files:
        sdrf['Comment[read1 file]'] = read1_files
        sdrf['Comment[read1 FASTQ_URI]'] = read1_paths
        sdrf['Comment[read2 file]'] = read2_files
        sdrf['Comment[read2 FASTQ_URI]'] = read2_paths
        if index1_files:
            sdrf['Comment[index1 file]'] = index1_files
            sdrf['Comment[index1 FASTQ_URI]'] = index1_paths
        else:
            sdrf['Comment[index1 file]'] = '' * len(read1_files)
            sdrf['Comment[index1 FASTQ_URI]'] = '' * len(read1_files)
        sdrf['Comment[SRA_URI]'] = '' * len(read1_files)
    elif sra_paths:
        sdrf['Comment[SRA_URI]'] = sra_paths
        sdrf['Comment[read1 file]'] = sra_read1_files
        sdrf['Comment[read2 file]'] = sra_read2_files
        sdrf['Comment[index1 file]'] = ''*len(sra_read1_files)
        sdrf['Comment[read1 FASTQ_URI]'] = ''*len(sra_read1_files)
        sdrf['Comment[read2 FASTQ_URI]'] = ''*len(sra_read1_files)
        sdrf['Comment[index1 FASTQ_URI]'] = ''*len(sra_read1_files)

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
    for accession in paths.keys():
        fastq = paths[accession]['files']
        for file in fastq:
            if '_R1' in file or '_R2' in file or '_R3' in file or '_R4' in file or '_I1' in file or '_I2' in file:
                if '_R1' in file:
                    paths_new[accession]['filename_read1'] = os.path.basename(file)
                    paths_new[accession]['filepath_read1'] = file
                if '_R2' in file:
                    paths_new[accession]['filename_read2'] = os.path.basename(file)
                    paths_new[accession]['filepath_read2'] = file
                if '_I1' in file or '_R3' in file:
                    paths_new[accession]['filename_index1'] = os.path.basename(file)
                    paths_new[accession]['filepath_index1'] = file
                if '_I2' in file or '_R4' in file:
                    paths_new[accession]['filename_index2'] = os.path.basename(file)
                    paths_new[accession]['filepath_index2'] = file
            elif '_1' in file or '_2' in file or '_3' in file or '_4' in file and '_R' not in file:
                if '_1' in file:
                    paths_new[accession]['filename_read1'] = os.path.basename(file)
                    paths_new[accession]['filepath_read1'] = file
                if '_2' in file:
                    paths_new[accession]['filename_read2'] = os.path.basename(file)
                    paths_new[accession]['filepath_read2'] = file
                if '_3' in file:
                    paths_new[accession]['filename_index1'] = os.path.basename(file)
                    paths_new[accession]['filepath_index1'] = file
                if '_4' in file:
                    paths_new[accession]['filename_index2'] = os.path.basename(file)
                    paths_new[accession]['filepath_index2'] = file
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
            result_list.append(pool.map(retrieve_paths_from_sra, run_lists))
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
                    if sra_status == '1' or 1:
                        file_name = sra_file.attrib['filename']
                        if 'SRR' in file_name:
                            accession = file_name
                            file_path = sra_file.attrib['url']
                            paths_sra[accession]['files'].append(file_path)
                        else:
                             continue
    except:
        paths_sra = None
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
        if sra_results.shape[0] > 0:
            for i, accession in enumerate(list(sra_results['run_accession'])):
                if accession in run_accessions:
                    paths_sra[accession] = {'files': []}
                    file_path = str(list(sra_results['sra_ftp'])[i])
                    file_path = "ftp://" + file_path
                    paths_sra[accession]['files'].append(file_path)
        else:
            paths_sra = {}
    except:
        paths_sra = {}
    return paths_sra

def get_fastq_path_from_ena(study_accession, run_accessions):
    paths_fastq = {}
    try:
        request_url = f'http://www.ebi.ac.uk/ena/portal/api/filereport?accession={study_accession}&result=read_run&fields=run_accession,fastq_ftp'
        fastq_results = pd.read_csv(request_url, delimiter='\t')
        if fastq_results.shape[0] > 0:
            for i in range(0, len(list(fastq_results['run_accession']))):
                accession = list(fastq_results['run_accession'])[i]
                if accession in run_accessions:
                    paths_fastq[accession] = {'files': []}
                    if ';' in str(list(fastq_results['fastq_ftp'])[i]):
                        # The fastq file paths are split by ";" when retrieved using the above ENA url. If there is no ';' separater,
                        # this means that the number of available fastq files is <= 1. 2 is the minimum number required. If only 1
                        # fastq file is available then an empty dictionary is returned.
                        file_list = str(list(fastq_results['fastq_ftp'])[i]).split(';')
                        for file_path in file_list:
                            file_path = "ftp://" + file_path
                            paths_fastq[accession]['files'].append(file_path)
                    else:
                            paths_fastq = {}
                else:
                    continue
    except:
        paths_fastq = paths_fastq
    return paths_fastq
