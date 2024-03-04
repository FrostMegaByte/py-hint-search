# import os
# import argparse
# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt


# def set_data_types(df: pd.DataFrame) -> pd.DataFrame:
#     # fmt: off
#     if df["# annotations after Pyright"].dtype == "object":
#         df["# annotations after Pyright"] = df["# annotations after Pyright"].astype(float)
#         df["# extra Pyright annotations"] = df["# extra Pyright annotations"].astype(float)

#     if df["# annotations after ML search"].dtype == "object":
#         df["# annotations after ML search"] = df["# annotations after ML search"].astype(float)
#         df["# extra ML search annotations"] = df["# extra ML search annotations"].astype(float)
#         df["% extra ML search annotations"] = df["% extra ML search annotations"].astype(float)
#         df["% extra ML search annotations after Pyright"] = df["% extra ML search annotations after Pyright"].astype(float)
#         df["Average time per ML search slot (s)"] = df["Average time per ML search slot (s)"].astype(float)
#     # fmt: on
#     return df


# def filter_rows(df: pd.DataFrame) -> pd.DataFrame:
#     # print(df.shape[0])
#     # Filter out the rows where the ML search didn't happen.
#     df = df[df["# extra ML search annotations"].notnull()]

#     # Filter out the rows where there are 3 or fewer fillable type slots.
#     # df = df[df["# fillable type slots"] > 3]

#     # Filter out the rows where 0 extra ML annotations were added because of timeout or not finding a correct value.
#     # df = df[df["# extra ML search annotations"] > 0]
#     # print(df.shape[0])
#     return df


# def main(project_path: str, all_or_project) -> None:
#     for i in [1]:
#         filename_reduced = f"all-evaluation-statistics-top{i}-reduced.csv"
#         csv_location_reduced = os.path.join(project_path, filename_reduced)
#         df_reduced = pd.read_csv(csv_location_reduced)

#         filename_typet5 = f"all-evaluation-statistics-top{i}-typet5.csv"
#         csv_location_typet5 = os.path.join(project_path, filename_typet5)
#         df_typet5 = pd.read_csv(csv_location_typet5)

#         # Replace all "-" values with NaN.
#         df_reduced = df_reduced.replace("-", np.nan)
#         df_typet5 = df_typet5.replace("-", np.nan)

#         # Set the data types of the columns.
#         df_reduced = set_data_types(df_reduced)
#         df_typet5 = set_data_types(df_typet5)
#         df_reduced = filter_rows(df_reduced)
#         df_typet5 = filter_rows(df_typet5)

#         plt.figure()  # Create a new figure each time
#         filtered_reduced = df_reduced[df_reduced["# fillable type slots"] <= 10]
#         filtered_typet5 = df_typet5[df_typet5["# fillable type slots"] <= 10]

#         _, _, before_handle = plt.hist(
#             filtered_typet5["# fillable type slots"], bins=10, alpha=0.6
#         )
#         _, _, after_reduced_handle = plt.hist(
#             filtered_reduced["# unfilled type slots"], bins=10, alpha=0.6
#         )
#         _, _, after_typet5_handle = plt.hist(
#             filtered_typet5["# unfilled type slots"], bins=10, alpha=0.6
#         )
#         plt.xlabel("Number of Unfilled Type Slots")
#         plt.ylabel("Frequency")
#         title = f"Number of Unfilled Type Slots - {'All Projects' if all_or_project == 'all' else all_or_project}"
#         plt.title(title)
#         plt.legend(
#             (before_handle, after_reduced_handle, after_typet5_handle),
#             ("Before", "After Reduced", "After TypeT5"),
#         )
#         plt.margins(x=0)
#         plt.show()

#         # plt.figure()  # Create a new figure each time
#         # filtered = df_typet5[df_typet5["# unfilled type slots"] <= 10]

#         # # Calculate counts for each category
#         # before_counts = filtered["# fillable type slots"].value_counts().sort_index()
#         # after_counts = filtered["# unfilled type slots"].value_counts().sort_index()

#         # # Define the bar positions and width
#         # bar_width = 0.35
#         # before_positions = np.arange(len(before_counts[:10]))
#         # after_positions = before_positions + bar_width

#         # # Create the bar chart
#         # plt.bar(
#         #     before_positions,
#         #     before_counts[:10],
#         #     width=bar_width,
#         #     alpha=0.6,
#         #     label="Before",
#         # )
#         # plt.bar(
#         #     after_positions,
#         #     after_counts[:10],
#         #     width=bar_width,
#         #     alpha=0.6,
#         #     label="After",
#         # )

#         # plt.xlabel("Number of Unfilled Type Slots")
#         # plt.ylabel("Frequency")
#         # title = f"Number of Unfilled Type Slots - {'All Projects' if all_or_project == 'all' else all_or_project}"
#         # plt.title(title)
#         # plt.legend()
#         # plt.margins(x=0)
#         # plt.xticks(
#         #     (before_positions + after_positions) / 2, before_counts.index
#         # )  # Set x-tick labels
#         # plt.show()
#         return

#         # fmt: off
#         stats = {
#             "Mean - # groundtruth annotations": df["# groundtruth annotations"].mean(),
#             "Mean - # annotations after Pyright": df["# annotations after Pyright"].mean(),
#             "Mean - # annotations after ML search": df["# annotations after ML search"].mean(),
#             "Mean - # fillable type slots": df["# fillable type slots"].mean(),
#             "Mean - # unfilled type slots": df["# unfilled type slots"].mean(),
#             "Mean - # total type slots": df["# total type slots"].mean(),
#             "Mean - # extra Pyright annotations": df["# extra Pyright annotations"].mean(),
#             "Mean - # extra ML search annotations": df["# extra ML search annotations"].mean(),
#             "Mean - % extra Pyright annotations": df["% extra Pyright annotations"].mean(),
#             "Mean - % extra ML search annotations": df["% extra ML search annotations"].mean(),
#             "Mean - % extra annotations (all)": df["% extra annotations (all)"].mean(),
#             "Mean - # ML search evaluated type slots": df["# ML search evaluated type slots"].mean(),
#             "Mean - % extra ML search annotations after Pyright": df["% extra ML search annotations after Pyright"].mean(),
#             "Mean - Pyright time (s)": df["Pyright time (s)"].mean(),
#             "Sum - Pyright time (s)": df["Pyright time (s)"].sum(),
#             "Mean - Average time per ML search slot (s)": df["Average time per ML search slot (s)"].mean(),
#             "Mean - ML search time (s)": df["ML search time (s)"].mean(),
#             "Sum - ML search time (s)": df["ML search time (s)"].sum(),
#             "Mean - Total time (s)": df["Total time (s)"].mean(),
#             "Sum - Total time (s)": df["Total time (s)"].sum(),
#             "Max - Peak memory usage Pyright (mb)": df["Peak memory usage Pyright (mb)"].max(),
#             "Max - Peak memory usage ML search (mb)": df["Peak memory usage ML search (mb)"].max(),
#         }
#         # fmt: on

#         annotation_groups = {
#             "ubiquitous-args": [
#                 df["# ubiquitous annotations parameters (groundtruth)"].sum(),
#                 df["# ubiquitous annotations parameters (extra Pyright)"].sum(),
#                 df["# ubiquitous annotations parameters (extra ML)"].sum(),
#                 df["# ubiquitous annotations parameters (all)"].sum(),
#             ],
#             "ubiquitous-returns": [
#                 df["# ubiquitous annotations returns (groundtruth)"].sum(),
#                 df["# ubiquitous annotations returns (extra Pyright)"].sum(),
#                 df["# ubiquitous annotations returns (extra ML)"].sum(),
#                 df["# ubiquitous annotations returns (all)"].sum(),
#             ],
#             "common-args": [
#                 df["# common annotations parameters (groundtruth)"].sum(),
#                 df["# common annotations parameters (extra Pyright)"].sum(),
#                 df["# common annotations parameters (extra ML)"].sum(),
#                 df["# common annotations parameters (all)"].sum(),
#             ],
#             "common-returns": [
#                 df["# common annotations returns (groundtruth)"].sum(),
#                 df["# common annotations returns (extra Pyright)"].sum(),
#                 df["# common annotations returns (extra ML)"].sum(),
#                 df["# common annotations returns (all)"].sum(),
#             ],
#             "rare-args": [
#                 df["# rare annotations parameters (groundtruth)"].sum(),
#                 df["# rare annotations parameters (extra Pyright)"].sum(),
#                 df["# rare annotations parameters (extra ML)"].sum(),
#                 df["# rare annotations parameters (all)"].sum(),
#             ],
#             "rare-returns": [
#                 df["# rare annotations returns (groundtruth)"].sum(),
#                 df["# rare annotations returns (extra Pyright)"].sum(),
#                 df["# rare annotations returns (extra ML)"].sum(),
#                 df["# rare annotations returns (all)"].sum(),
#             ],
#         }

#         TOP_N_INDEPENDENT = [
#             "Mean - # groundtruth annotations",
#             "Mean - # annotations after Pyright",
#             "Mean - # fillable type slots",
#             "Mean - # total type slots",
#             "Mean - # extra Pyright annotations",
#             "Mean - % extra Pyright annotations",
#             "Mean - Pyright time (s)",
#             "Sum - Pyright time (s)",
#             "Mean - # ML search evaluated type slots",
#         ]

#         if i == 1:
#             print(f"General top-n independent stats:")
#             for indep_stat in TOP_N_INDEPENDENT:
#                 print(f"{stats[indep_stat]:.2f} \t-> {str(indep_stat)}")
#             print()

#         print(f"Top {i}:")
#         for key, value in stats.items():
#             if key not in TOP_N_INDEPENDENT:
#                 print(f"{value:.2f}\t\t-> {key}")

#         print()
#         print("Most important stats:")
#         print(
#             "Mean - # extra Pyright annotations:",
#             round(stats["Mean - # extra Pyright annotations"], 2),
#         )
#         print(
#             "Mean - % extra Pyright annotations:",
#             round(stats["Mean - % extra Pyright annotations"], 2),
#         )
#         print(
#             "Mean - # extra ML search annotations:",
#             round(stats["Mean - # extra ML search annotations"], 2),
#         )
#         print(
#             "Mean - % extra ML search annotations:",
#             round(stats["Mean - % extra ML search annotations"], 2),
#         )
#         print(
#             "Mean - % extra ML search annotations after Pyright:",
#             round(stats["Mean - % extra ML search annotations after Pyright"], 2),
#         )
#         print()

#         annotation_groups_table = pd.DataFrame(
#             annotation_groups, index=["groundtruth", "extra Pyright", "extra ML", "all"]
#         ).round(2)
#         print(annotation_groups_table)
#         print()


# def parse_arguments(project) -> argparse.Namespace:
#     parser = argparse.ArgumentParser(description="")

#     def dir_path(string: str) -> str:
#         if os.path.isdir(string):
#             return string
#         else:
#             raise NotADirectoryError(string)

#     if project == "all":
#         parser.add_argument(
#             "--project-path",
#             type=dir_path,
#             default=os.getcwd(),
#             help="The path to the evaluation statistics CSVs.",
#         )
#     else:
#         parser.add_argument(
#             "--project-path",
#             type=dir_path,
#             default=os.path.join(
#                 os.getcwd(), project, "logs-evaluation/fully-annotated"
#             ),
#             help="The path to the evaluation statistics CSVs.",
#         )

#     return parser.parse_args()


# if __name__ == "__main__":
#     all_or_project = "all"
#     args = parse_arguments(all_or_project)
#     main(args.project_path, all_or_project)
