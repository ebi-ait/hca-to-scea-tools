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

def get_fastq_path_from_ena(run_accessions):
    paths_fastq = {}
    for accession in run_accessions:
        request_url = f'http://www.ebi.ac.uk/ena/portal/api/filereport?accession={accession}&result=read_run&fields=run_accession,fastq_ftp,sra_ftp,submitted_ftp'
        fastq_results = pd.read_csv(request_url, delimiter='\t')
        fastq_results = fastq_results.dropna(axis=1, how='all')
        url_col = [col for col in ['fastq_ftp', 'sra_ftp', 'submitted_ftp'] if col in fastq_results.columns][0]
        if len(fastq_results) == 0:
            return {}
        paths_fastq[accession] = {'files': []}
        file_list = str(fastq_results[url_col].values[0]).split(';')
        # TODO skip per file not whole project
        if len(file_list) < 2:
            return {}
        for file_path in file_list:
            paths_fastq[accession]['files'].append(f"ftp://{file_path}")
    return paths_fastq
