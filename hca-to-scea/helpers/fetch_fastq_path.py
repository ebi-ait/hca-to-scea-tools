import argparse
import os
import requests as rq
from xml.etree import ElementTree
import multiprocessing
from contextlib import contextmanager
import pandas as pd

from json_files.library_dicts import default_read_lengths as DEFAULT_READ_LENGTHS

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

def get_filename_from_xml_run(xml_run):
    return [srafile.attrib['filename'] for srafile in xml_run.findall(".//SRAFile")]

def add_index_filenames(sorted_filenames, default_index_dict):
    return {key: sorted_filenames[i] for i, key in enumerate(default_index_dict.keys()) if i < len(sorted_filenames)}

def get_sra_fastq_lengths_by_default_length(run_accessions, technology, default_read_lengths=DEFAULT_READ_LENGTHS):
    """Retrieve the FASTQ file lengths and compare with default read lengths.
        If expected read lengths are matched, we can assume that sra files read index is as in default_read_lengths.
        param run_accessions: list of SRA run accessions
        param technology: library preparation technology used in experiment (should be compatible with technology_dict)
        param default_read_lengths: dictionary of default read lengths by specific technologies
        output: dictionary mapping SRA run accessions to their FASTQ file lengths, read_index, and boolean for successful mapping
    """
    if technology not in default_read_lengths:
        raise ValueError(f"Technology {technology} not supported (add to default_read_lengths dictionary).")
    expected_read_lengths = list(default_read_lengths[technology].values())

    url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch/fcgi?db=sra&id={",".join(run_accessions)}'
    response = rq.get(url)
    if not response.ok:
        raise ValueError(f"Failed to retrieve SRA data for {run_accessions}")
    root = ElementTree.fromstring(response.content)

    results = {}
    for run in root.findall(".//RUN"):
        run_accession = run.attrib['accession']
        if run_accession in run_accessions:
            print(run_accession)
            read_lengths = []

            for read in run.findall(".//Statistics/Read"):
                avg_len = int(read.attrib["average"])
                read_lengths.append(avg_len)

            results[run_accession] = {"read_lengths": read_lengths}
            filenames = [sra_filename for sra_filename in get_filename_from_xml_run(run) if 'fastq' in sra_filename]
            if read_lengths == expected_read_lengths:
                results[run_accession]["filenames"] = add_index_filenames(filenames, default_read_lengths[technology])
                results[run_accession]["read_map"] = True
            elif set(read_lengths) == set(expected_read_lengths):
                reindex = [read_lengths.index(read_len) for read_len in expected_read_lengths]
                _, reordered_filenames = zip(*sorted(zip(reindex, filenames)))
                results[run_accession]["filenames"] = add_index_filenames(reordered_filenames, default_read_lengths[technology])
                results[run_accession]["read_map"] = True
            else:
                results[run_accession]["filenames"] = add_index_filenames(filenames, default_read_lengths[technology])
                results[run_accession]["read_map"] = False

    return results

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
    request_url = f'http://www.ebi.ac.uk/ena/portal/api/filereport?accession={study_accession}&result=read_run&fields=run_accession,fastq_ftp,sra_ftp,submitted_ftp'
    fastq_results = pd.read_csv(request_url, delimiter='\t')
    fastq_results = fastq_results.dropna(axis=1, how='all')
    url_col = [col for col in ['fastq_ftp', 'sra_ftp', 'submitted_ftp'] if col in fastq_results.columns][0]
    for accession in run_accessions:
        paths_fastq[accession] = {'files': []}
        if accession not in fastq_results['run_accession'].values:
            continue
        fastq_result = fastq_results[fastq_results['run_accession'] == accession]
        file_list = str(fastq_result[url_col].values[0]).split(';')
        # TODO skip per file not whole project
        if len(file_list) < 2:
            return {}
        for file_path in file_list:
            paths_fastq[accession]['files'].append(f"ftp://{file_path}")
    return paths_fastq
