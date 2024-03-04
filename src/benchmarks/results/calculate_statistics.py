import os
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def set_data_types(df: pd.DataFrame) -> pd.DataFrame:
    # fmt: off
    if df["# annotations after Pyright"].dtype == "object":
        df["# annotations after Pyright"] = df["# annotations after Pyright"].astype(float)
        df["# extra Pyright annotations"] = df["# extra Pyright annotations"].astype(float)
        
    if df["# annotations after ML search"].dtype == "object":
        df["# annotations after ML search"] = df["# annotations after ML search"].astype(float)
        df["# extra ML search annotations"] = df["# extra ML search annotations"].astype(float)
        df["% extra ML search annotations"] = df["% extra ML search annotations"].astype(float)
        df["% extra ML search annotations after Pyright"] = df["% extra ML search annotations after Pyright"].astype(float)
        df["Average time per ML search slot (s)"] = df["Average time per ML search slot (s)"].astype(float)
    # fmt: on
    return df


def filter_rows(df: pd.DataFrame) -> pd.DataFrame:
    # print(df.shape[0])
    # Filter out the rows where the ML search didn't happen.
    df = df[df["# extra ML search annotations"].notnull()]

    # Filter out the rows where there are 3 or fewer fillable type slots.
    # df = df[df["# fillable type slots"] > 3]

    # Filter out the rows where 0 extra ML annotations were added because of timeout or not finding a correct value.
    # df = df[df["# extra ML search annotations"] > 0]
    return df


def main(project_path: str, all_or_project) -> None:
    for i in [1, 3, 5]:
        filename = (
            f"all-evaluation-statistics-top{i}.csv"
            if all_or_project == "all"
            else f"evaluation-statistics-top{i}.csv"
        )
        csv_location = os.path.join(project_path, filename)
        df = pd.read_csv(csv_location)

        # Replace all "-" values with NaN.
        df = df.replace("-", np.nan)

        # Set the data types of the columns.
        df = set_data_types(df)
        df = filter_rows(df)

        # df = df.drop(["file"], axis=1)
        # filtered = df.groupby(["project"]).mean()

        plt.figure()  # Create a new figure each time
        filtered = df[df["# fillable type slots"] <= 100]
        _, _, before_handle = plt.hist(
            filtered["# fillable type slots"], bins=100, alpha=0.6
        )
        _, _, after_handle = plt.hist(
            filtered["# unfilled type slots"], bins=100, alpha=0.6
        )
        plt.xlabel("Number of Unfilled Type Slots")
        plt.ylabel("Frequency")
        title = f"Number of Unfilled Type Slots - {'All Projects' if all_or_project == 'all' else all_or_project}"
        plt.title(title)
        plt.legend(
            (before_handle, after_handle),
            ("Before", "After"),
        )
        plt.margins(x=0)
        # plt.xlim(0, 60)
        plt.xscale("symlog")
        plt.show()

        # fmt: off
        stats = {
            "Mean - # groundtruth annotations": df["# groundtruth annotations"].mean(),
            "Mean - # annotations after Pyright": df["# annotations after Pyright"].mean(),
            "Mean - # annotations after ML search": df["# annotations after ML search"].mean(),
            "Mean - # fillable type slots": df["# fillable type slots"].mean(),
            "Mean - # unfilled type slots after Pyright": df["# fillable type slots"].mean() - df["# extra Pyright annotations"].mean(),
            "Mean - # unfilled type slots after ML search": df["# unfilled type slots"].mean(),
            "Mean - # total type slots": df["# total type slots"].mean(),
            "Mean - # extra Pyright annotations": df["# extra Pyright annotations"].mean(),
            "Mean - # extra ML search annotations": df["# extra ML search annotations"].mean(),
            "Mean - % extra Pyright annotations": df["# extra Pyright annotations"].mean() / df["# fillable type slots"].mean() * 100,
            "Mean - % extra ML search annotations": df["# extra ML search annotations"].mean() / df["# fillable type slots"].mean() * 100,
            "Mean - % extra annotations (all)": (df["# annotations after ML search"].mean() - df["# groundtruth annotations"].mean()) / df["# fillable type slots"].mean() * 100,
            "Mean - # ML search evaluated type slots": df["# ML search evaluated type slots"].mean(),
            "Mean - % extra ML search annotations after Pyright": df["# extra ML search annotations"].mean() / df["# ML search evaluated type slots"].mean() * 100,
            "Mean - Pyright time (s)": df["Pyright time (s)"].mean(),
            "Sum - Pyright time (s)": df["Pyright time (s)"].sum(),
            "Mean - Average time per ML search slot (s)": df["Average time per ML search slot (s)"].mean(),
            "Mean - ML search time (s)": df["ML search time (s)"].mean(),
            "Sum - ML search time (s)": df["ML search time (s)"].sum(),
            "Mean - Total time (s)": df["Total time (s)"].mean(),
            "Sum - Total time (s)": df["Total time (s)"].sum(),
            "Max - Peak memory usage Pyright (mb)": df["Peak memory usage Pyright (mb)"].max(),
            "Max - Peak memory usage ML search (mb)": df["Peak memory usage ML search (mb)"].max(),
        }
        # fmt: on

        annotation_groups = {
            "ubiquitous-args": [
                df["# ubiquitous annotations parameters (groundtruth)"].sum(),
                df["# ubiquitous annotations parameters (extra Pyright)"].sum(),
                df["# ubiquitous annotations parameters (extra ML)"].sum(),
                df["# ubiquitous annotations parameters (all)"].sum(),
            ],
            "ubiquitous-returns": [
                df["# ubiquitous annotations returns (groundtruth)"].sum(),
                df["# ubiquitous annotations returns (extra Pyright)"].sum(),
                df["# ubiquitous annotations returns (extra ML)"].sum(),
                df["# ubiquitous annotations returns (all)"].sum(),
            ],
            "common-args": [
                df["# common annotations parameters (groundtruth)"].sum(),
                df["# common annotations parameters (extra Pyright)"].sum(),
                df["# common annotations parameters (extra ML)"].sum(),
                df["# common annotations parameters (all)"].sum(),
            ],
            "common-returns": [
                df["# common annotations returns (groundtruth)"].sum(),
                df["# common annotations returns (extra Pyright)"].sum(),
                df["# common annotations returns (extra ML)"].sum(),
                df["# common annotations returns (all)"].sum(),
            ],
            "rare-args": [
                df["# rare annotations parameters (groundtruth)"].sum(),
                df["# rare annotations parameters (extra Pyright)"].sum(),
                df["# rare annotations parameters (extra ML)"].sum(),
                df["# rare annotations parameters (all)"].sum(),
            ],
            "rare-returns": [
                df["# rare annotations returns (groundtruth)"].sum(),
                df["# rare annotations returns (extra Pyright)"].sum(),
                df["# rare annotations returns (extra ML)"].sum(),
                df["# rare annotations returns (all)"].sum(),
            ],
        }

        all_type_annotations_without_dunder_methods = (
            df["# ubiquitous annotations parameters (all)"].sum()
            + df["# ubiquitous annotations returns (all)"].sum()
            + df["# common annotations parameters (all)"].sum()
            + df["# common annotations returns (all)"].sum()
            + df["# rare annotations parameters (all)"].sum()
            + df["# rare annotations returns (all)"].sum()
        )

        # fmt: off
        annotation_groups_percentages = {
            "ubiquitous-args %": [
                df["# ubiquitous annotations parameters (groundtruth)"].sum() / all_type_annotations_without_dunder_methods * 100,
                df["# ubiquitous annotations parameters (extra Pyright)"].sum() / all_type_annotations_without_dunder_methods * 100,
                df["# ubiquitous annotations parameters (extra ML)"].sum() / all_type_annotations_without_dunder_methods * 100,
                df["# ubiquitous annotations parameters (all)"].sum() / all_type_annotations_without_dunder_methods * 100,
            ],
            "ubiquitous-returns %": [
                df["# ubiquitous annotations returns (groundtruth)"].sum() / all_type_annotations_without_dunder_methods * 100,
                df["# ubiquitous annotations returns (extra Pyright)"].sum() / all_type_annotations_without_dunder_methods * 100,
                df["# ubiquitous annotations returns (extra ML)"].sum() / all_type_annotations_without_dunder_methods * 100,
                df["# ubiquitous annotations returns (all)"].sum() / all_type_annotations_without_dunder_methods * 100,
            ],
            "common-args %": [
                df["# common annotations parameters (groundtruth)"].sum() / all_type_annotations_without_dunder_methods * 100,
                df["# common annotations parameters (extra Pyright)"].sum() / all_type_annotations_without_dunder_methods * 100,
                df["# common annotations parameters (extra ML)"].sum() / all_type_annotations_without_dunder_methods * 100,
                df["# common annotations parameters (all)"].sum() / all_type_annotations_without_dunder_methods * 100,
            ],
            "common-returns %": [
                df["# common annotations returns (groundtruth)"].sum() / all_type_annotations_without_dunder_methods * 100,
                df["# common annotations returns (extra Pyright)"].sum() / all_type_annotations_without_dunder_methods * 100,
                df["# common annotations returns (extra ML)"].sum() / all_type_annotations_without_dunder_methods * 100,
                df["# common annotations returns (all)"].sum() / all_type_annotations_without_dunder_methods * 100,
            ],
            "rare-args %": [
                df["# rare annotations parameters (groundtruth)"].sum() / all_type_annotations_without_dunder_methods * 100,
                df["# rare annotations parameters (extra Pyright)"].sum() / all_type_annotations_without_dunder_methods * 100,
                df["# rare annotations parameters (extra ML)"].sum() / all_type_annotations_without_dunder_methods * 100,
                df["# rare annotations parameters (all)"].sum() / all_type_annotations_without_dunder_methods * 100,
            ],
            "rare-returns %": [
                df["# rare annotations returns (groundtruth)"].sum() / all_type_annotations_without_dunder_methods * 100,
                df["# rare annotations returns (extra Pyright)"].sum() / all_type_annotations_without_dunder_methods * 100,
                df["# rare annotations returns (extra ML)"].sum() / all_type_annotations_without_dunder_methods * 100,
                df["# rare annotations returns (all)"].sum() / all_type_annotations_without_dunder_methods * 100,
            ],
        }
        # annotation_groups_percentages = {
        #     "ubiquitous-args": df["# ubiquitous annotations parameters (all)"].sum() / all_type_annotations_without_dunder_methods * 100,
        #     "ubiquitous-returns": df["# ubiquitous annotations returns (all)"].sum() / all_type_annotations_without_dunder_methods * 100,
        #     "common-args": df["# common annotations parameters (all)"].sum() / all_type_annotations_without_dunder_methods * 100,
        #     "common-returns": df["# common annotations returns (all)"].sum() / all_type_annotations_without_dunder_methods * 100,
        #     "rare-args": df["# rare annotations parameters (all)"].sum() / all_type_annotations_without_dunder_methods * 100,
        #     "rare-returns": df["# rare annotations returns (all)"].sum() / all_type_annotations_without_dunder_methods * 100,
        # }
        # fmt: on

        TOP_N_INDEPENDENT = [
            "Mean - # groundtruth annotations",
            "Mean - # annotations after Pyright",
            "Mean - # fillable type slots",
            "Mean - # unfilled type slots after Pyright",
            "Mean - # total type slots",
            "Mean - # extra Pyright annotations",
            "Mean - % extra Pyright annotations",
            "Mean - Pyright time (s)",
            "Sum - Pyright time (s)",
            "Mean - # ML search evaluated type slots",
        ]

        if i == 1:
            print(f"General top-n independent stats:")
            for indep_stat in TOP_N_INDEPENDENT:
                print(f"{stats[indep_stat]:.2f} \t-> {str(indep_stat)}")
            print()

        print(f"Top {i}:")
        for key, value in stats.items():
            if key not in TOP_N_INDEPENDENT:
                print(f"{value:.2f}\t\t-> {key}")

        print()
        print("Most important stats:")
        print(
            "Mean - # extra Pyright annotations:",
            round(stats["Mean - # extra Pyright annotations"], 2),
        )
        print(
            "Mean - % extra Pyright annotations:",
            round(stats["Mean - % extra Pyright annotations"], 2),
        )
        print(
            "Mean - # extra ML search annotations:",
            round(stats["Mean - # extra ML search annotations"], 2),
        )
        print(
            "Mean - % extra ML search annotations:",
            round(stats["Mean - % extra ML search annotations"], 2),
        )
        print(
            "Mean - % extra ML search annotations after Pyright:",
            round(stats["Mean - % extra ML search annotations after Pyright"], 2),
        )
        print()

        annotation_groups_table = pd.DataFrame(
            annotation_groups, index=["groundtruth", "extra Pyright", "extra ML", "all"]
        ).round(2)
        print(annotation_groups_table)
        print()
        annotation_groups_percentages_table = pd.DataFrame(
            annotation_groups_percentages,
            index=["groundtruth", "extra Pyright", "extra ML", "all"],
        ).round(1)
        print(annotation_groups_percentages_table)
        print()


def parse_arguments(project) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="")

    def dir_path(string: str) -> str:
        if os.path.isdir(string):
            return string
        else:
            raise NotADirectoryError(string)

    if project == "all":
        parser.add_argument(
            "--project-path",
            type=dir_path,
            default=os.getcwd(),
            help="The path to the evaluation statistics CSVs.",
        )
    else:
        parser.add_argument(
            "--project-path",
            type=dir_path,
            default=os.path.join(
                os.getcwd(), project, "logs-evaluation/fully-annotated"
            ),
            help="The path to the evaluation statistics CSVs.",
        )

    return parser.parse_args()


if __name__ == "__main__":
    while True:
        all_or_project = input("Enter a value 'all' or project name): ")
        if all_or_project in ["all"] + os.listdir("."):
            break
        print("Invalid input. Please enter 'all' or a project name: ")

    args = parse_arguments(all_or_project)
    main(args.project_path, all_or_project)
