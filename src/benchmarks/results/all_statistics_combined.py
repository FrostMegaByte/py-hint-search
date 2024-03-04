import os
import csv


def create_evaluation_csv_file(output_file) -> None:
    headers = [
        "project",
        "file",
        "# groundtruth annotations",
        "# annotations after Pyright",
        "# annotations after ML search",
        "# fillable type slots",
        "# unfilled type slots",
        "# total type slots",
        "# extra Pyright annotations",
        "# extra ML search annotations",
        f"% extra Pyright annotations",
        f"% extra ML search annotations",
        f"% extra annotations (all)",
        "# ML search evaluated type slots",
        f"% extra ML search annotations after Pyright",
        "Pyright time (s)",
        "Average time per ML search slot (s)",
        "ML search time (s)",
        "Total time (s)",
        "Peak memory usage Pyright (mb)",
        "Peak memory usage ML search (mb)",
        "# ubiquitous annotations parameters (groundtruth)",
        "# ubiquitous annotations returns (groundtruth)",
        "# common annotations parameters (groundtruth)",
        "# common annotations returns (groundtruth)",
        "# rare annotations parameters (groundtruth)",
        "# rare annotations returns (groundtruth)",
        "# ubiquitous annotations parameters (extra Pyright)",
        "# ubiquitous annotations returns (extra Pyright)",
        "# common annotations parameters (extra Pyright)",
        "# common annotations returns (extra Pyright)",
        "# rare annotations parameters (extra Pyright)",
        "# rare annotations returns (extra Pyright)",
        "# ubiquitous annotations parameters (extra ML)",
        "# ubiquitous annotations returns (extra ML)",
        "# common annotations parameters (extra ML)",
        "# common annotations returns (extra ML)",
        "# rare annotations parameters (extra ML)",
        "# rare annotations returns (extra ML)",
        "# ubiquitous annotations parameters (all)",
        "# ubiquitous annotations returns (all)",
        "# common annotations parameters (all)",
        "# common annotations returns (all)",
        "# rare annotations parameters (all)",
        "# rare annotations returns (all)",
    ]
    with open(
        output_file,
        "w",
        newline="",
    ) as file:
        writer = csv.writer(file)
        writer.writerow(headers)


def append_evaluation_statistics(top_n):
    # Define the paths
    base_dir = "D:/Documents/TU Delft/Year 6/Master's Thesis/Results from GCP"
    output_file = os.path.join(base_dir, f"all-evaluation-statistics-top{top_n}.csv")

    # Create CSV file
    create_evaluation_csv_file(output_file)

    # Iterate through directories
    for dirpath, dirnames, filenames in os.walk(base_dir):
        if "#BACKUP" in dirnames:
            dirnames.remove("#BACKUP")  # Exclude #BACKUP directory

        log_dir = os.path.join(dirpath, "logs-evaluation/fully-annotated")
        if os.path.exists(log_dir):
            csv_file = os.path.join(log_dir, f"evaluation-statistics-top{top_n}.csv")
            if os.path.isfile(csv_file):
                project_name = os.path.relpath(dirpath, base_dir)
                if project_name not in os.listdir(base_dir):
                    print(f"{project_name} not found")
                    continue

                # Open the CSV file and append its contents to the output file
                with open(csv_file, "r", newline="") as infile:
                    reader = csv.reader(infile)
                    next(reader)  # Skip header
                    with open(output_file, "a", newline="") as outfile:
                        writer = csv.writer(outfile)
                        for row in reader:
                            row.insert(0, project_name)
                            writer.writerow(row)


# Main function
def main():
    while True:
        top_n = int(input("Enter a value (1, 3 or 5): "))
        if top_n in (1, 3, 5):
            break
        print("Invalid input. Please enter 1, 3 or 5.")
    append_evaluation_statistics(top_n)


if __name__ == "__main__":
    main()
