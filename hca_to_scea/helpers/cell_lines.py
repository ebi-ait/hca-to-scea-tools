import pandas as pd
import sys

def get_specimen(xlsx_dict, type):

    specimen_df = xlsx_dict['specimen_from_organism'].merge(
        xlsx_dict[type],
        how="outer",
        on="specimen_from_organism.biomaterial_core.biomaterial_id"
    )

    return specimen_df

def merge_cell_lines(xlsx_dict, merged_df, experimental_design):

    if experimental_design == "cell_line_only":

        merged_df = xlsx_dict['cell_line'].merge(
            merged_df,
            how="outer",
            on="cell_line.biomaterial_core.biomaterial_id"
        )

        specimen_df = get_specimen(xlsx_dict, type="cell_line")
        merged_df = merged_df.merge(
            specimen_df,
            how="outer",
            on="cell_line.biomaterial_core.biomaterial_id"
            )

    elif experimental_design == "organoid_only":

        merged_df = xlsx_dict['organoid'].merge(
            merged_df,
            how="outer",
            on="organoid.biomaterial_core.biomaterial_id"
        )

        specimen_df = get_specimen(xlsx_dict, type="organoid")
        merged_df = merged_df.merge(
            specimen_df,
            how="outer",
            on="cell_line.biomaterial_core.biomaterial_id"
            )

    elif experimental_design == "organoid":

        merged_df = xlsx_dict['organoid'].merge(
            merged_df,
            how="outer",
            on="organoid.biomaterial_core.biomaterial_id"
        )

        merged_df = xlsx_dict['cell_line'].merge(
            merged_df,
            how="outer",
            on="cell_line.biomaterial_core.biomaterial_id"
        )

        specimen_df = get_specimen(xlsx_dict, type="cell_line")
        merged_df = merged_df.merge(
            specimen_df,
            how="outer",
            on="cell_line.biomaterial_core.biomaterial_id"
            )

    return merged_df