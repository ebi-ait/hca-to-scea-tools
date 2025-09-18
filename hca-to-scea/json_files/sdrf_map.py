minimum_map = {
    "Characteristics[organism]": "donor_organism.genus_species.ontology_label",
    "Characteristics[individual]": "donor_organism.biomaterial_core.biomaterial_id",
    "Characteristics[sex]": "donor_organism.sex",
    "Characteristics[age]": "donor_organism.organism_age",
    "Unit[time unit]": "donor_organism.organism_age_unit.text",
    "Characteristics[developmental stage]": "donor_organism.development_stage.text",
    "Characteristics[organism part]": "specimen_from_organism.organ.ontology_label",
    "Characteristics[sampling site]": "specimen_from_organism.organ_parts.ontology_label",
    "Characteristics[disease]": "donor_organism.diseases.ontology_label",
    "Characteristics[organism status]": "donor_organism.is_living",
    "Characteristics[cause of death]": "donor_organism.death.cause_of_death",
}

accessions_dict = {
    'Comment[BioSD_SAMPLE]': 'cell_suspension.biomaterial_core.biosamples_accession',
    'Comment[ENA_SAMPLE]': 'cell_suspension.insdc_experiment.insdc_sample_accession',
    'Comment[ENA_EXPERIMENT]': 'cell_suspension.insdc_experiment.insdc_experiment_accession',
    'Comment[ENA_RUN]': 'sequence_file.insdc_run_accessions',
    'Comment[technical replicate group]': 'cell_suspension.biomaterial_core.biosamples_accession'
}

map_exp_designs = {
    "standard": {
        "Characteristics[cell type]": "cell_suspension.selected_cell_types.ontology_label",
        "Description": "specimen_from_organism.biomaterial_core.biomaterial_description"
    },
    "organoid": {
        "Characteristics[cell line]": "organoid.biomaterial_core.biomaterial_name",
        "Characteristic[growth condition]": "cell_line.growth_conditions.growth_medium",
        "Characteristic[progenitor cell type]": "cell_line.cell_type.text",
        "Characteristics[treatment]": "organoid.growth_conditions.drug_treatment",
        "Characteristics[cell type]": "organoid.model_organ.ontology_label",
        "Description": "organoid.biomaterial_core.biomaterial_description",
    },
    "cell_line": {
        "Characteristics[cell line]": "cell_line.biomaterial_core.biomaterial_name",
        "Characteristic[growth condition]": "cell_line.growth_conditions.growth_medium",
        "Characteristic[progenitor cell type]": "cell_line.cell_type.text",
        "Characteristics[treatment]": "cell_line.growth_conditions.drug_treatment",
        "Characteristics[cell type]": "cell_line.model_organ.ontology_label",
        "Description": "cell_line.biomaterial_core.biomaterial_description",
    },
    "cell_line_organoid": {
        "Characteristics[cell line]": "cell_line.biomaterial_core.biomaterial_name",
        "Characteristic[growth condition]": "cell_line.growth_conditions.growth_medium",
        "Characteristic[progenitor cell type]": "cell_line.cell_type.text",
        "Characteristics[treatment]": "organoid.growth_conditions.drug_treatment",
        "Characteristics[cell type]": "organoid.model_organ.ontology_label",
        "Description": "organoid.biomaterial_core.biomaterial_description",
    }
}

factor_mapppings = {
    "disease": "specimen_from_organism.diseases.ontology_label",
    "development stage": "donor_organism.development_stage.text",
    "sampling_time": "specimen_from_organism.collection_time",
    "organ": "specimen_from_organism.organ.ontology_label",
    "organ_part": "specimen_from_organism.organ_parts.ontology_label",
    "cell_type": "cell_suspension.selected_cell_types.ontology_label",
}