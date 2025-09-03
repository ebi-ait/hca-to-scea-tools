import pandas as pd
import sys

def get_specimen(xlsx_dict, type):

    specimen_df = xlsx_dict['specimen_from_organism'].merge(
        xlsx_dict[type],
        how="outer",
        on="specimen_from_organism.biomaterial_core.biomaterial_id"
    )

    return specimen_df

def fix_overlap(df):
    for col_x in df.columns:
        if col_x.endswith("_x"):
            fixed_col = col_x[:-2]
            col_y = fixed_col + "_y"
            df[fixed_col] = df[col_x].combine_first(df[col_y])
            df = df.drop(columns=[col_x, col_y], axis=1)
    return df

def merge_cell_lines(xlsx_dict, merged_df, experimental_design):

    if experimental_design == "cell_line_only":

        merged_df = xlsx_dict['cell_line'].merge(
            merged_df,
            how="outer",
            on="cell_line.biomaterial_core.biomaterial_id"
        )
        merged_df = fix_overlap(merged_df)

        specimen_df = get_specimen(xlsx_dict, type="cell_line")
        merged_df = merged_df.merge(
            specimen_df,
            how="outer",
            on="cell_line.biomaterial_core.biomaterial_id"
            )
        merged_df = fix_overlap(merged_df)

    elif experimental_design == "organoid_only":

        merged_df = xlsx_dict['organoid'].merge(
            merged_df,
            how="outer",
            on="organoid.biomaterial_core.biomaterial_id"
        )
        merged_df = fix_overlap(merged_df)

        specimen_df = get_specimen(xlsx_dict, type="organoid")
        merged_df = merged_df.merge(
            specimen_df,
            how="outer",
            on="cell_line.biomaterial_core.biomaterial_id"
            )
        merged_df = fix_overlap(merged_df)

    elif experimental_design == "organoid":

        merged_df = xlsx_dict['organoid'].merge(
            merged_df,
            how="outer",
            on="organoid.biomaterial_core.biomaterial_id"
        )
        merged_df = fix_overlap(merged_df)

        merged_df = xlsx_dict['cell_line'].merge(
            merged_df,
            how="outer",
            on="cell_line.biomaterial_core.biomaterial_id"
        )
        merged_df = fix_overlap(merged_df)

        specimen_df = get_specimen(xlsx_dict, type="cell_line")
        merged_df = merged_df.merge(
            specimen_df,
            how="outer",
            on="cell_line.biomaterial_core.biomaterial_id"
            )
        merged_df = fix_overlap(merged_df)

    return merged_df