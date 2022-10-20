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
        if biomaterial in xlsx_dict.keys():
            species_key = "%s.genus_species.ontology_label" % (biomaterial)
            species_list.extend(list(xlsx_dict[biomaterial][species_key].values))
    species_list = list(set(species_list))
    species_list = [x for x in species_list if str(x) != 'nan']

    assert all("||" not in s for s in species_list),"The dataset contains biomaterials linked to >1 species (pooled). To be eligible for SCEA each biomaterial must be" \
                                                    " linked to 1 species only (Human or Mouse). Please remove the relevant biomaterials from the dataset" \
                                                    " and run again."

    assert all(s in ["Homo sapiens","Mus musculus"] for s in species_list),"1 or more species are not eligible. Species must be" \
                                                                           " either Homo sapiens or Mus musculus."

    assert len(species_list) == 1,"Only 1 species is allowed per SCEA E-HCAD id. " \
                                      "Please split the dataset by species and run them separately."

def check_biomaterial_linkings(xlsx_dict):

    biomaterial_tabs = ["donor_organism", "specimen_from_organism", "cell_line", "organoid", "cell_suspension"]
    biomaterial_tabs = [tab for tab in biomaterial_tabs if tab in xlsx_dict.keys()]

    biomaterial_id_dict = {}
    for biomaterial_tab in biomaterial_tabs:

        biomaterial_id_dict[biomaterial_tab] = {"ids":[],"input_tabs":[],"input_ids":[]}
        biomaterial_id_dict[biomaterial_tab]["ids"] = list(xlsx_dict[biomaterial_tab]["%s.biomaterial_core.biomaterial_id" % (biomaterial_tab)])
        biomaterial_id_key = "%s.biomaterial_core.biomaterial_id" % (biomaterial_tab)
        biomaterial_id_dict[biomaterial_tab]["input_tabs"] = [tab for tab in biomaterial_tabs if biomaterial_id_key in xlsx_dict[tab].columns]
        biomaterial_id_dict[biomaterial_tab]["input_tabs"].remove(biomaterial_tab)
        for tab in biomaterial_id_dict[biomaterial_tab]["input_tabs"]:
            biomaterial_id_dict[biomaterial_tab]["input_ids"].extend(xlsx_dict[tab][biomaterial_id_key])
        if biomaterial_id_key in xlsx_dict["sequence_file"].columns:
            biomaterial_id_dict[biomaterial_tab]["input_ids"].extend(list(xlsx_dict["sequence_file"][biomaterial_id_key]))

        for id in biomaterial_id_dict[biomaterial_tab]["ids"]:
            assert id in biomaterial_id_dict[biomaterial_tab]["input_ids"],"Biomaterial id %s is an orphan biomaterial. Please fix the linking" \
                                                                           " and run again." % (id)

def check_protocol_linkings(xlsx_dict):

    protocol_tabs = ["collection_protocol", "dissociation_protocol", "enrichment_protocol", "differentiation_protocol", "library_preparation_protocol", "sequencing_protocol"]
    biomaterial_tabs = ["donor_organism", "specimen_from_organism", "cell_line", "organoid", "cell_suspension", "sequence_file"]

    protocol_id_dict = {}
    for protocol_tab in protocol_tabs:
        if protocol_tab in xlsx_dict.keys():
            protocol_id_key = "%s.protocol_core.protocol_id" % (protocol_tab)
            protocol_id_dict[protocol_tab] = {"ids":[],"input_ids":[]}
            protocol_id_dict[protocol_tab]["ids"] = list(xlsx_dict[protocol_tab][protocol_id_key])
            for biomaterial_tab in biomaterial_tabs:
                if biomaterial_tab in xlsx_dict.keys():
                    if protocol_id_key in xlsx_dict[biomaterial_tab].columns:
                        protocol_id_dict[protocol_tab]["input_ids"].extend(list(xlsx_dict[biomaterial_tab][protocol_id_key]))

            input_ids = [item for item in protocol_id_dict[protocol_tab]["input_ids"] if str(item) != 'nan']
            for input_id in input_ids:
                if "||" in input_id:
                    new_input_ids = input_id.split("||")
                    protocol_id_dict[protocol_tab]["input_ids"].extend(new_input_ids)

            protocol_id_dict[protocol_tab]["input_ids"] = set(protocol_id_dict[protocol_tab]["input_ids"])

            for id in protocol_id_dict[protocol_tab]["ids"]:
                assert id in protocol_id_dict[protocol_tab]["input_ids"], "Protocol id %s is an orphan protocol. Please fix the linking" \
                          " and run again." % (id)

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
            cell_suspension_ids = list(xlsx_dict["cell_suspension"][key])
            cell_suspension_ids = [x for x in cell_suspension_ids if str(x) != 'nan']
            if len(cell_suspension_ids) >= 1:
                input_types.append(biomaterial)
    input_types = list(set(input_types))
    assert len(input_types) == 1,"All inputs to cell suspensions should be of an identical biomaterial type." \
                           " For example, cell suspensions should all be linked to cell lines only, organoids only" \
                           " or specimens only. Please split the dataset by the input biomaterial type."

def check_cell_lines_linked(xlsx_dict):

    cell_line_key = "cell_line.biomaterial_core.biomaterial_id"
    specimen_key = "specimen_from_organism.biomaterial_core.biomaterial_id"

    assert specimen_key in xlsx_dict["cell_line"].columns,"Cell_lines are not linked to" \
                                                 " a specimen id. Please link all cell_lines to an input specimen."

    # Check that cell lines are not linked to an input cell line
    for column in xlsx_dict["cell_line"].columns:
        if "cell_line.biomaterial_core.biomaterial_id." in column:
            cell_line_as_input = [x for x in list(xlsx_dict["cell_line"][column]) if str(x) != 'nan']
            assert len(cell_line_as_input) == 0," Cell line input biomaterial type should be specimen id. Cell line cannot be used" \
                                                " as input to a cell line."

    input_specimen_ids = [x for x in list(xlsx_dict["cell_line"][specimen_key]) if str(x) != 'nan']
    cell_line_ids = list(xlsx_dict["cell_line"][cell_line_key])
    assert len(input_specimen_ids) == len(cell_line_ids),"1 more more cell_lines are not linked to" \
                                                 " a specimen id. Please link all cell_lines to an input specimen."

def check_organoids_linked(xlsx_dict):

    if "specimen_from_organism.biomaterial_core.biomaterial_id" in xlsx_dict["organoid"].columns:
        input_specimen_ids = [x for x in list(xlsx_dict["organoid"]["specimen_from_organism.biomaterial_core.biomaterial_id"]) if str(x) != 'nan']
    else:
        input_specimen_ids = []

    if "cell_line.biomaterial_core.biomaterial_id" in xlsx_dict["organoid"].columns:
        input_cell_line_ids = [x for x in list(xlsx_dict["organoid"]["cell_line.biomaterial_core.biomaterial_id"]) if str(x) != 'nan']
    else:
        input_cell_line_ids = []

    # Check that organoids are not linked to an input organoid
    for column in xlsx_dict["organoid"].columns:
        if "organoid.biomaterial_core.biomaterial_id." in column:
            organoid_as_input = [x for x in list(xlsx_dict["organoid"][column]) if str(x) != 'nan']
            assert len(organoid_as_input) == 0,"Organoid input biomaterial type should be specimen id or cell line id. Organoid cannot be used" \
                                                " as input to an organoid."

    # Check that all organoid ids are linked to the same input biomaterial type; all specimen ids or all cell line ids.
    if len(input_cell_line_ids) > 0:
        assert len(input_specimen_ids) == 0,"Organoids are linked to more than 1 input biomaterial type. Please link all organoids" \
                                                                        " to 1 input biomaterial type (specimen or cell line). The dataset cen be split by biomaterial type" \
                                                                         " if needed."
    if len(input_specimen_ids) > 0:
        assert len(input_cell_line_ids) == 0,"Organoids are linked to more than 1 input biomaterial type. Please link all organoids" \
                                                                        " to 1 input biomaterial type (specimen or cell line). The dataset cen be split by biomaterial type" \
                                                                        " if needed."

    # Check that all organoid ids are linked to a specimen id or a cell line id.
    organoid_ids = list(xlsx_dict["organoid"]["organoid.biomaterial_core.biomaterial_id"])
    assert len(input_specimen_ids) == len(organoid_ids) or len(input_cell_line_ids) == len(organoid_ids),"1 more more organoids are not linked to" \
                                                 " a specimen id or cell line id. Please link all organoids to an input specimen or cell line."

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
