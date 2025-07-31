# HCA to SCEA Ingest Collector and Argument Generator

This repository provides a script to automate
1. the selection of eligible projects from HCA DCP ingest
2. the preparation of metadata arguments required for the script in hca-to-scea

## Project Structure

```
├── get_hca2scea_info.py # Main script to collect summary metadata
├── get_hca2scea_args.py # Main script to generate SCEA arguments
├── hca_spreadsheets/ # Directory where downloaded Excel files are saved
└── README.md
```

## Requirements

Python 3.8+

Install dependencies:

```bash
pip install pandas openpyxl requests hca-ingest tqdm

```

## Usage of info
To run the `get_hca2scea_info.py` script:

```bash
python script_name.py
```

## Usage of args
The `get_hca2scea_args.py` script can run in two modes.

To process all UUIDs listed in the 'hca_submissions_summary.csv' generated from previous script:
```bash
python get_hca2scea_args.py -c INITIALS --token YOUR_API_TOKEN
```
To process a single submission UUID:

```bash
python generate_scea_args.py -u SUBMISSION_UUID -c INITIALS --token YOUR_API_TOKEN
```
