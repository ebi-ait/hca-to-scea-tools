def check_technology_eligibility(xlsx_dict,technology_dict):

    technology_types = list(xlsx_dict["library_preparation_protocol"]["library_preparation_protocol.library_construction_method.ontology_label"].values)
    assert all(t in technology_dict.keys() for t in technology_types),"1 or more technology types are not eligible." \
                                                               " Please remove ineligible technologies and their linked" \
                                                               " samples and try again."

    assert len(technology_types) == 1,"Only 1 technology type is allowed per SCEA E-HCAD id. " \
                                      "Please split the dataset by the technology type and run them separately."

def check_species_eligibility(xlsx_dict):

    biomaterial_tab = ["donor_organism","specimen_from_organism","cell_line","organoid","cell_suspension"]

    species_list = []
    for biomaterial in biomaterial_tab:
        species_key = "%s.genus_species.ontology_label" % (biomaterial)
        species_list.extend(list(xlsx_dict[biomaterial][species_key].values))
    species_list = list(set(species_list))
    species_list = [x for x in species_list if str(x) != 'nan']

    assert all("||" not in s for s in species_list),"The dataset contains biomaterials linked to >1 species (pooled). To be elgiible for SCEA, each biomaterial must be" \
                                                    " linked to 1 species only (Human or Mouse). Please remove the relevant biomaterials from the dataset" \
                                                    " and run again."

    assert all(s in ["Homo sapiens","Mus musculus"] for s in species_list),"1 or more species are not eligible. Species must be" \
                                                                           " either Homo sapiens or Mus musculus."

    assert len(species_list) == 1,"Only 1 species is allowed per SCEA E-HCAD id. " \
                                      "Please split the dataset by species and run them separately."

def check_for_pooled_samples(xlsx_dict):

    biomaterial_tab = ["donor_organism","specimen_from_organism","cell_line","organoid","cell_suspension"]

    input_biomaterial_list = []
    for biomaterial in biomaterial_tab:
        for key in biomaterial_tab:
            input_biomaterial_key = "%s.biomaterial_core.biomaterial_id" % (key)
            if input_biomaterial_key in xlsx_dict[biomaterial].keys():
                input_biomaterial_list.extend(list(xlsx_dict[biomaterial][input_biomaterial_key].values))
    input_biomaterial_list = list(set(input_biomaterial_list))
    input_biomaterial_list = [x for x in input_biomaterial_list if str(x) != 'nan']
    print(input_biomaterial_list)

    assert all("||" not in i for i in input_biomaterial_list),"The dataset contains pooled biomaterials. Pooled biomaterials are not eligible." \
                                                              " Please remove the relevant biomaterials from the dataset " \
                                                              " and run again."

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