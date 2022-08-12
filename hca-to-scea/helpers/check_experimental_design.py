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

    assert all("||" not in i for i in input_biomaterial_list),"The dataset contains pooled biomaterials. Pooled biomaterials are not eligible." \
                                                              " Please remove the relevant biomaterials from the dataset " \
                                                              " and run again."

def check_donor_exists(xlsx_dict):

    assert 'donor_organism' in xlsx_dict.keys(),"The dataset does not include donor organism biomaterials." \
                                                        " Cell lines, organoids and cell suspensions must be derived from a specimen linked" \
                                                        " to a donor." \
                                                        ""

    assert len(list(xlsx_dict['donor_organism']['donor_organism.biomaterial_core.biomaterial_id'])) >= 1,"The dataset does not include donor_organism biomaterials." \
                                                        " Cell lines, organoids and cell suspensions must be derived from a specimen linked" \
                                                        " to a donor." \
                                                        ""

def check_specimen_exists(xlsx_dict):

    assert 'specimen_from_organism' in xlsx_dict.keys(),"The dataset does not include specimen_from_organism biomaterials." \
                                                        " Cell lines, organoids and cell suspensions must be derived from a specimen linked" \
                                                        " to a donor." \
                                                        ""

    assert len(list(xlsx_dict['specimen_from_organism']['specimen_from_organism.biomaterial_core.biomaterial_id'])) >= 1,"The dataset does not include specimen_from_organism biomaterials." \
                                                        " Cell lines, organoids and cell suspensions must be derived from a specimen linked" \
                                                        " to a donor." \
                                                        ""

def check_input_to_cell_suspension(xlsx_dict):

    biomaterials = ["specimen_from_organism","cell_line","organoid"]
    input_types = []
    for biomaterial in biomaterials:
        key = "%s.biomaterial_core.biomaterial_id" % biomaterial
        if key in xlsx_dict["cell_suspension"].columns:
            if len(list(xlsx_dict["cell_suspension"][key])) >= 1:
                input_types.append(biomaterial)
    input_types = set(input_types)
    assert input_types == 1,"All inputs to cell suspensions should be of an identical biomaterial type." \
                           "For example, cell suspensions should all be linked to cell lines only, organoids only" \
                           "or specimens only. Please split the dataset by the input biomaterial type."

#def check_cell_lines_linked_to_specimen():
#all cell lines should be linked to a specimen

#def check_input_to_cell_suspension(xlsx_dict)
# #all organoids should be linked to a specimen or a cell line. The
# type should be the same for all organoids.

def get_experimental_design(xlsx_dict: {}):

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

    if cell_line and not organoid:
        experimental_design = "cell_line_only"
    elif not cell_line and organoid:
        experimental_design = "organoid_only"
    elif cell_line and organoid:
        experimental_design = "organoid"
    else:
        experimental_design = "standard"

    return experimental_design