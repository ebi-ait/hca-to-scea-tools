import copy
import pandas as pd

from hca_to_scea.helpers import check_experimental_design

def filter_biomaterials(xlsx_dict, xlsx_dict_tmp, library_protocol):

    xlsx_dict_tmp["sequence_file"] = xlsx_dict["sequence_file"].loc[
        xlsx_dict["sequence_file"]["library_preparation_protocol.protocol_core.protocol_id"] == library_protocol]
    cell_suspension_ids = xlsx_dict_tmp["sequence_file"]["cell_suspension.biomaterial_core.biomaterial_id"].values
    xlsx_dict_tmp["cell_suspension"] = xlsx_dict["cell_suspension"][
        xlsx_dict["cell_suspension"]["cell_suspension.biomaterial_core.biomaterial_id"].isin((cell_suspension_ids))]

    biomaterial_tabs = ["specimen_from_organism", "organoid", "cell_line"]
    for biomaterial_tab in biomaterial_tabs:
        if biomaterial_tab in xlsx_dict.keys():
            if not xlsx_dict_tmp[biomaterial_tab].empty:
                id_column = "{}.biomaterial_core.biomaterial_id".format(biomaterial_tab)
                if id_column in xlsx_dict_tmp["cell_suspension"].columns:
                    if not xlsx_dict_tmp["cell_suspension"][id_column].empty and not xlsx_dict_tmp["cell_suspension"][id_column].isna().all():
                        specimen_ids = xlsx_dict_tmp["cell_suspension"][
                            "{}.biomaterial_core.biomaterial_id".format(biomaterial_tab)].values
                        xlsx_dict_tmp[biomaterial_tab] = xlsx_dict[biomaterial_tab][
                            xlsx_dict[biomaterial_tab]["{}.biomaterial_core.biomaterial_id".format(biomaterial_tab)].isin(
                                (specimen_ids))]
                if "donor_organism.biomaterial_core.biomaterial_id" in xlsx_dict_tmp[biomaterial_tab].columns:
                    donor_ids_specimen = xlsx_dict_tmp[biomaterial_tab][
                        "donor_organism.biomaterial_core.biomaterial_id"].values
                    xlsx_dict_tmp["donor_organism"] = xlsx_dict["donor_organism"][
                        xlsx_dict["donor_organism"]["donor_organism.biomaterial_core.biomaterial_id"].isin(
                            (donor_ids_specimen))]

    return xlsx_dict_tmp

def filter_protocols(xlsx_dict_tmp):

    biomaterial_tabs = ["specimen_from_organism", "organoid", "cell_line", "cell_suspension", "sequence_file"]
    protocol_tabs = ["collection_protocol","dissociation_protocol","enrichment_protocol","differentiation_protocol","library_preparation_protocol","sequencing_protocol"]

    for protocol_tab in protocol_tabs:
        if protocol_tab in xlsx_dict_tmp.keys():
            id_column = "{}.protocol_core.protocol_id".format(protocol_tab)
            protocol_id_list = []
            for biomaterial_tab in biomaterial_tabs:
                if biomaterial_tab in xlsx_dict_tmp.keys():
                    if id_column in xlsx_dict_tmp[biomaterial_tab].columns:
                        protocol_id_list.extend(list(xlsx_dict_tmp[biomaterial_tab][id_column]))
            protocol_id_list = list(set(protocol_id_list))
            protocol_id_list = [protocol_id for protocol_id in protocol_id_list if pd.notnull(protocol_id)]
            protocol_id_split = [protocol_id.split("||") for protocol_id in protocol_id_list if "||" in protocol_id]
            if protocol_id_split:
                protocol_id_split = [item for sublist in protocol_id_split for item in sublist]
                protocol_id_split.extend([protocol_id for protocol_id in protocol_id_list if "||" not in protocol_id])
                protocol_id_list = protocol_id_split
            keep_protocols = [protocol_id for protocol_id in list(xlsx_dict_tmp[protocol_tab][id_column]) if protocol_id in protocol_id_list]
            xlsx_dict_tmp[protocol_tab] = xlsx_dict_tmp[protocol_tab][xlsx_dict_tmp[protocol_tab][id_column].isin((keep_protocols))]

    return xlsx_dict_tmp

def split_metadata_by_technology(xlsx_dict, technology_dict):

    '''Check for ineligible technoloy types and remove them from the library preparation protocol tab.'''
    for i in range(0,xlsx_dict["library_preparation_protocol"].shape[0]):
        library_protocol_technology = xlsx_dict["library_preparation_protocol"]["library_preparation_protocol.library_construction_method.ontology_label"][i]
        eligible = check_experimental_design.check_technology_eligibility(library_protocol_technology,technology_dict)
        if eligible == "False":
            xlsx_dict["library_preparation_protocol"].drop(xlsx_dict["library_preparation_protocol"].index[i])

    '''Get the list of eligible unique library preparation protocol types.'''
    if xlsx_dict["library_preparation_protocol"].empty:
        print("The library preparation technology type is not compatible. Please speak to Ami.")
        sys.exit()
    else:
        library_protocol_ids = xlsx_dict["library_preparation_protocol"]["library_preparation_protocol.protocol_core.protocol_id"].values
        list_xlsx_dict = []
        for library_protocol in library_protocol_ids:
            xlsx_dict_tmp = copy.deepcopy(xlsx_dict)
            xlsx_dict_tmp = filter_biomaterials(xlsx_dict,xlsx_dict_tmp,library_protocol)
            xlsx_dict_tmp2 = copy.deepcopy(xlsx_dict_tmp)
            xlsx_dict_tmp3 = filter_protocols(xlsx_dict_tmp2)
            list_xlsx_dict.append(xlsx_dict_tmp3)

    return list_xlsx_dict

def get_related_scea_accessions(accession, related_scea_accessions):

    if related_scea_accessions:
        related_scea_accessions = [str(accession.split("E-HCAD-")[0]) + str(related_scea_acc) for related_scea_acc in related_scea_accessions]
        if related_scea_accession:
            related_scea_accessions.extend(related_scea_accession)

    return related_scea_accessions