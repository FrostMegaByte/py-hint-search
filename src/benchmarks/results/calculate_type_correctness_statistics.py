import os
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def set_data_types(df: pd.DataFrame) -> pd.DataFrame:
    # fmt: off
    df["precision"] = df["precision"].astype(float)
    df["recall"] = df["recall"].astype(float)
    # fmt: on
    return df


def filter_rows(df: pd.DataFrame) -> pd.DataFrame:
    # print(df.shape[0])
    # Filter out the rows where the ML search didn't happen.
    df = df[df["# groundtruth annotations (excl. dunder methods)"] > 0]

    # Filter out the rows where there are 3 or fewer fillable type slots.
    # df = df[df["# fillable type slots"] > 3]

    # Filter out the rows where 0 extra ML annotations were added because of timeout or not finding a correct value.
    # df = df[df["# extra ML search annotations"] > 0]
    # print(df.shape[0])
    return df


def main(project_path: str, all_or_project) -> None:
    for i in [1, 3, 5]:
        filename = (
            f"all-type-correctness-top{i}.csv"
            if all_or_project == "all"
            else f"type-correctness-top{i}.csv"
        )
        csv_location = os.path.join(project_path, filename)
        df = pd.read_csv(csv_location)

        # Replace all "-" values with NaN.
        df = df.replace("-", np.nan)

        # Set the data types of the columns.
        df = set_data_types(df)
        df = filter_rows(df)

        mean_df = df.groupby(["metric"])[
            [
                "# groundtruth annotations (excl. dunder methods)",
                "# added PyHintSearch annotations (excl. dunder methods)",
                "# correct",
                "# incorrect",
            ]
        ].mean()
        mean_df["precision"] = (
            mean_df["# correct"]
            / mean_df["# added PyHintSearch annotations (excl. dunder methods)"]
        )
        mean_df["recall"] = (
            mean_df["# correct"]
            / mean_df["# groundtruth annotations (excl. dunder methods)"]
        )

        print(mean_df.round(2))
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
            default=os.path.join(os.getcwd(), project, "logs-evaluation"),
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
