def get_experimental_design(xlsx_dict: {}):

    if 'specimen_from_organism' in xlsx_dict.keys():
        if xlsx_dict['specimen_from_organism'].empty:
            specimen = False
        else:
            specimen = True
    else:
        specimen = False

    if 'cell_line' in xlsx_dict.keys():
        if xlsx_dict['cell_line'].empty:
            cell_line = False
        else:
            cell_line = True
    else:
        cell_line = False

    if 'organoid' in xlsx_dict.keys():
        if xlsx_dict['organoid'].empty:
            organoid = False
        else:
            organoid = True
    else:
        organoid = False

    if specimen:

        if cell_line and not organoid:
            experimental_design = "cell_line_only"
        elif not cell_line and organoid:
            experimental_design = "organoid_only"
        elif cell_line and organoid:
            experimental_design = "organoid"
        else:
            experimental_design = "standard"

    return experimental_design

def check_for_pooled_samples(xlsx_dict):

    specimen_metadata = xlsx_dict["specimen_from_organism"]
    specimen_ids = list(specimen_metadata['specimen_from_organism.biomaterial_core.biomaterial_id'])
    pooled_samples_specimen = [specimen_id for specimen_id in specimen_ids if "||" in specimen_id]

    pooled_samples_cell_line = []
    if "cell_line" in xlsx_dict.keys() and not xlsx_dict["cell_line"].empty:
        cell_line_metadata = xlsx_dict["cell_line"]
        if 'cell_line.biomaterial_core.biomaterial_id' in cell_line_metadata.columns:
            cell_line_ids = list(cell_line_metadata['cell_line.biomaterial_core.biomaterial_id'])
            pooled_samples_cell_line = [cell_line_id for cell_line_id in cell_line_ids if "||" in cell_line_id]

    pooled_samples_organoid = []
    if "organoid" in xlsx_dict.keys() and not xlsx_dict["organoid"].empty:
        organoid_metadata = xlsx_dict["organoid"]
        if 'organoid.biomaterial_core.biomaterial_id' in organoid_metadata.columns:
            organoid_ids = list(organoid_metadata['organoid.biomaterial_core.biomaterial_id'])
            pooled_samples_organoid = [organoid_id for organoid_id in organoid_ids if "||" in organoid_id]

    donor_metadata = xlsx_dict["donor_organism"]
    donor_ids = list(donor_metadata['donor_organism.biomaterial_core.biomaterial_id'])
    pooled_samples_donor = [str(donor_id) for donor_id in donor_ids if "||" in str(donor_id)]

    if pooled_samples_specimen or pooled_samples_donor or pooled_samples_cell_line or pooled_samples_organoid:
        pooled_samples = True
    else:
        pooled_samples = False

    return pooled_samples

def check_technology_eligibility(library_method,technology_dict):

    eligible = library_method in technology_dict.keys()

    return eligible