import os
import csv


def create_evaluation_csv_file(output_file) -> None:
    headers = [
        "project",
        "file",
        "metric",
        "# groundtruth annotations (excl. dunder methods)",
        "# added PyHintSearch annotations (excl. dunder methods)",
        "# correct",
        "# incorrect",
        "precision",
        "recall",
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
    output_file = os.path.join(base_dir, f"all-type-correctness-top{top_n}.csv")

    # Create CSV file
    create_evaluation_csv_file(output_file)

    # Iterate through directories
    for dirpath, dirnames, filenames in os.walk(base_dir):
        if "#BACKUP" in dirnames:
            dirnames.remove("#BACKUP")  # Exclude #BACKUP directory
        if "typet5" in dirnames:
            dirnames.remove("typet5")  # Exclude typet5 directory

        log_dir = os.path.join(dirpath, "logs-evaluation")
        if os.path.exists(log_dir):
            csv_file = os.path.join(log_dir, f"type-correctness-top{top_n}.csv")
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
