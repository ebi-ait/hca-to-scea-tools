import time
import requests

import pandas as pd
from hca_ingest.api.ingestapi import IngestApi
from tqdm import tqdm

# Setup
INGEST_API_URL = "https://api.ingest.archive.data.humancellatlas.org/"
CELLXGENE_API_URL = "https://api.cellxgene.cziscience.com/curation/v1/collections"
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
            'doi': [pub.get('doi') for pub in project['content'].get('publications', []) if pub.get('doi')],
            'cxg_link': any('cellxgene' in l for l in project['content'].get('supplementary_links', []))
        }
    except Exception as e:
        print(f"⚠️ Error fetching project metadata for submission {subm['uuid']['uuid']}: {e}")
        return {'project_uuid': None, 'short_name': None, 'wranglingState': 'UNKNOWN', 'geo_series_accessions': [], 'doi': [], 'cxg_link': False}

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

def get_cellxgene_data():
    try:
        response = requests.get(CELLXGENE_API_URL, timeout=30)
        response.raise_for_status()
        collections = response.json()
        
        # Build both DataFrame and lookup dictionaries
        cxg_data = []
        doi_to_id = {}
        gse_to_id = {}
        
        for c in collections:
            collection_id = c['collection_id']
            doi = c['doi'].lower() if isinstance(c.get('doi'), str) else None
            gse_list = [l['link_name'] for l in c.get('links', [])
                        if l.get('link_name', '').startswith('GSE')]
            
            cxg_data.append({
                'collection_id': collection_id,
                'doi': doi,
                'gse': gse_list
            })
            
            if doi:
                doi_to_id[doi] = collection_id
            for gse in gse_list:
                gse_to_id[gse] = collection_id
        
        return pd.DataFrame(cxg_data)
    except Exception as e:
        print(f"⚠️ Cellxgene API error: {str(e)}")
        return None

def match_cxg_identifier(cxg_df, identifier, id_type='doi'):
    if id_type not in ['doi', 'gse']:
        raise ValueError("id_type must be 'doi' or 'gse'")
    if id_type == 'doi':
        identifier = identifier.lower()
        return cxg_df.loc[cxg_df['doi'] == identifier, 'collection_id'].values[0]
    elif id_type == 'gse':
        return cxg_df.loc[cxg_df['gse'].apply(lambda x: identifier in x), 'collection_id'].values[0]
    return None

def main():
    # NCBI Taxon IDs of interest
    taxon_ids = [9606, 10900, 9607, 9060, 9615]

    # Result Data Frame
    ing_dict = {
        'subm_uuid': [],
        'project_uuid': [],
        'project_id': [],
        'project_short_name': [],
        'cxg_link': False,
        'cxg_doi': None,
        'cxg_geo': None,
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
    for subm in tqdm(submissions[0:2], desc="Processing submissions", unit="submission"):
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

    # --- Cellxgene data ---
    t0 = time.time()
    print("🔍 Fetching Cellxgene collections...")
    cxg_df = get_cellxgene_data()
    cxg_df.to_csv("all_cellxgene_collections.csv", index=False)
    print(f"🔢 Recovered {len(cxg_df)} collections!")
    print("🔸 Matching Cellxgene data...", flush=True)
    df['cxg_doi'] = df['doi'].apply(lambda x: [match_cxg_identifier(cxg_df, doi, 'doi') for doi in x if doi in cxg_df['doi'].values])
    df['cxg_doi'] = df['cxg_doi'].apply(lambda x: x[0] if x else False)
    df['cxg_geo'] = df['geo_series_accessions'].apply(lambda x: [match_cxg_identifier(cxg_df, gse, 'gse') for gse in x if gse in cxg_df['gse'].values])
    df['cxg_geo'] = df['cxg_geo'].apply(lambda x: x[0] if x else False)
    print(f"🔹 Cellxgene matching done in {time.time() - t0:.2f}s")

    # --- Save and report ---
    filename = "hca_submissions_summary.csv"
    df.to_csv(f"{filename}", index=False)

    total_time = time.time() - overall_time
    print(f"\n✅ Done! Processed {len(df)} submissions in {total_time:.1f}s")
    print(f"📄 Output written to: {filename}")

if __name__ == "__main__":
    main()