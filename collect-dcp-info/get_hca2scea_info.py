import time
import requests
import pandas as pd
from hca_ingest.api.ingestapi import IngestApi
from tqdm import tqdm
from datetime import datetime

# Setup
INGEST_API_URL = "https://api.ingest.archive.data.humancellatlas.org/"
token = "<token>"

def get_valid_api(token=None):
    api = IngestApi(INGEST_API_URL)
    api.set_token(f"Bearer {token}")
    response = requests.get(f"{INGEST_API_URL}/submissionEnvelopes/", headers=api.get_headers())
    while response.status_code != 200:
        token = input("Please provide a valid token:").strip()
        api.set_token(f"Bearer {token}")
        response = requests.get(f"{INGEST_API_URL}/submissionEnvelopes/", headers=api.get_headers())
        print("Invalid token.")
    return api

def get_all(post_response, query):
    """Paginate through POST results using 'next' link."""
    all_files = post_response['_embedded']['files']
    while 'next' in post_response['_links']:
        post_response = api.post(post_response['_links']['next']['href'], json=query).json()
        all_files.extend(post_response['_embedded']['files'])
    return all_files

def get_project_metadata(api, subm):
    try:
        project = api.get(subm['_links']['projects']['href']).json()['_embedded']['projects'][0]
        return {
            'project_uuid': project['uuid']['uuid'],
            'project_id': project['_links']['self']['href'].rstrip('/').split('/')[-1],
            'short_name': project['content']['project_core'].get('project_short_name', None),
            'wranglingState': project['wranglingState'] if project['wranglingState'] in ['Published in DCP', 'Submitted'] else subm.get('submissionState', None),
            'geo_series_accessions': project['content'].get('geo_series_accessions', []),
            'doi': [pub.get('doi') for pub in project['content'].get('publications', []) if pub.get('doi')]
        }
    except Exception as e:
        print(f"⚠️ Error fetching project metadata for submission {subm['uuid']['uuid']}: {e}")
        return {'project_uuid': None, 'short_name': None, 'wranglingState': 'UNKNOWN', 'geo_series_accessions': [], 'doi': []}

def library_methods(api, project_id):
    try:
        prot_query = [
            {
                "field": "content.library_construction_method.text",
                "operator": "REGEX",
                "value": ".*"
            },
            {
                "field": "project.id",
                "operator": "IS",
                "value": project_id
            }
        ]
        response = api.post(f"{INGEST_API_URL}/protocols/query?operator=AND", json=prot_query)
        protocols = response.json().get('_embedded', {}).get('protocols', []) if response.ok else []
        return set(p.get("content", {}).get("library_construction_method", {}).get("ontology_label", "text but no label!") for p in protocols)
    except Exception as e:
        print(f"⚠️ Error fetching library methods for project {project_id}: {e}")
        return set()
    
def taxa_ids(api, project_id, taxon_ids):
    found_taxa = set()
    try:
        for taxon in taxon_ids:
            bm_query = [
                {
                    "field": "content.biomaterial_core.ncbi_taxon_id",
                    "operator": "IS",
                    "value": taxon
                },
                {
                    "field": "project.id",
                    "operator": "IS",
                    "value": project_id
                }
            ]
            bm_response = api.post(f"{INGEST_API_URL}/biomaterials/query?operator=AND", json=bm_query)
            if bm_response.ok and bm_response.json().get('_embedded', {}).get('biomaterials'):
                found_taxa.add(str(taxon))
    except Exception as e:
        print(f"⚠️ Error fetching taxa for project {project_id}: {e}")
    return found_taxa

def fastq_counter(api, project_id):
    try:
        seq_query = [
            {
                "field": "content.insdc_run_accessions",
                "operator": "REGEX",
                "value": ".*"
            },
            {
                "field": "describedBy",
                "operator": "REGEX",
                "value": ".*/sequence_file$"
            },
            {
                "field": "project.id",
                "operator": "IS",
                "value": project_id
            }
        ]
        seq_response = api.post(f"{INGEST_API_URL}/files/query?operator=AND", json=seq_query)
        return seq_response.json()['page']['totalElements'] if seq_response.ok else 0
    except Exception as e:
        print(f"⚠️ Error fetching FASTQ count for project {project_id}: {e}")
        return 0
    
def analysis_types(api, project_id):
    try:
        analysis_query = [
            {
                "field": "content.file_core.content_description.ontology",
                "operator": "NIN",
                "value": ['EDAM:3917','data:3917','EDAM:1270','data:1270','EFO:0010198','EDAM:3112','data:3112']
            },
            {
                "field": "describedBy",
                "operator": "REGEX",
                "value": ".*/analysis_file$"
            },
            {
                "field": "project.id",
                "operator": "IS",
                "value": project_id
            }
        ]
        analysis_response = api.post(f"{INGEST_API_URL}/files/query?operator=AND", json=analysis_query)

        files = []
        analysis_descriptions = set()
        if analysis_response.ok and analysis_response.json()['page']['totalElements'] > 0:
            files = get_all(analysis_response.json(), analysis_query)
            print(f"analysis: {analysis_response.json()['page']['totalElements']}", flush=True, end=' ')
        for f in files:
            descriptions = f.get("content", {}).get("file_core", {}).get("content_description", [])
            for d in descriptions:
                if d.get("text"):
                    analysis_descriptions.add(d["text"])
        return "||".join(sorted(analysis_descriptions))
    except Exception as e:
        print(f"\n⚠️ File query error in project {row['project_uuid']}: {e}")
        return ""
    

def main():
    # NCBI Taxon IDs of interest
    taxon_ids = [9606, 10900, 9607, 9060, 9615]

    # Result Data Frame
    ing_dict = {
        'subm_uuid': [],
        'project_uuid': [],
        'project_id': [],
        'project_short_name': [],
        'cxg': [],
        'wranglingState': [],
        'doi': [],
        'geo_series_accessions': [],
        'azul_valid': [],
        'lib_prots': [],
        'organisms': [],
        'insdc_fastqs': [],
        'analysis_types': []
    }
    df = pd.DataFrame(ing_dict)

    api = get_valid_api(token)

    # Get all submission envelopes
    print("🔍 Fetching all submission envelopes...")
    submissions = list(api.get_all(f"{INGEST_API_URL}/submissionEnvelopes", "submissionEnvelopes"))

    print(f"🔢 Total submissions: {len(submissions)}\n")

    overall_time = time.time()
    for subm in tqdm(submissions, desc="Processing submissions", unit="submission"):
        row = {}
        sub_start = time.time()
        sub_uuid = subm['uuid']['uuid']
        row['subm_uuid'] = sub_uuid

        # --- Project Info ---
        t0 = time.time()
        print("🔸 Get project...", flush=True)
        row.update(get_project_metadata(api, subm))
        print(f"🔹 Project fetched in {time.time() - t0:.2f}s")

        # --- Azul validation ---
        t0 = time.time()
        print("🔸 Check Azul...", flush=True)
        azul_resp = requests.get(f"https://service.azul.data.humancellatlas.org/index/projects/{row['project_uuid']}")
        row.update({'azul_valid': azul_resp.ok})
        print(f"🔹 Azul check done in {time.time() - t0:.2f}s")

        # --- Protocols (library methods) ---
        t0 = time.time()
        print("🔸 Get library methods...", flush=True)
        lib_methods = library_methods(api, row['project_id'])
        row.update({'lib_prots': "||".join(sorted(lib_methods))})
        print(f"🔹 Library methods fetched in {time.time() - t0:.2f}s")

        # --- Biomaterials (organisms) ---
        t0 = time.time()
        print("🔸 Get taxa...", flush=True)
        found_taxa = taxa_ids(api, row['project_id'], taxon_ids)
        row.update({'organisms': "||".join(sorted(found_taxa))})
        print(f"🔹 Taxa fetched in {time.time() - t0:.2f}s")

        # --- Sequence files ---
        t0 = time.time()
        print("🔸 Get files...", flush=True)
        row.update({'insdc_fastqs': fastq_counter(api, row['project_id'])})
        print(f"🔹 Files fetched in {time.time() - t0:.2f}s")

        # --- Analysis files ---
        t0 = time.time()
        print("🔸 Get analysis files...", flush=True)
        row.update({'analysis_types': analysis_types(api, row['project_id'])})
        print(f"🔹 Analysis files fetched in {time.time() - t0:.2f}s")

        # --- Append results ---
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

        sub_elapsed = time.time() - sub_start
        tqdm.write(f"⏱️ {sub_uuid} processed in {sub_elapsed:.1f}s")

    # --- Save and report ---
    filename = "hca_submissions_summary.csv"
    df.to_csv(f"{filename}", index=False)

    total_time = time.time() - overall_time
    print(f"\n✅ Done! Processed {len(df)} submissions in {total_time:.1f}s")
    print(f"📄 Output written to: {filename}")

if __name__ == "__main__":
    main()