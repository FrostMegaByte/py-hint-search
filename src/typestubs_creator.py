import os
import subprocess


def create_typestubs(project_path):
    base_dir = project_path.rsplit("/", 1)[0]
    python_subdirectories = get_subdirectories(project_path)
    python_subdirectories.reverse()
    os.chdir(base_dir)

    for subdirectory in python_subdirectories:
        subdirectory_path = os.path.join(base_dir, subdirectory)
        init_file_path = os.path.join(subdirectory_path, "__init__.py")
        init_file_exists = os.path.exists(init_file_path)

        # Create __init__.py file if it doesn't exist yet
        if not init_file_exists:
            with open(init_file_path, "w") as f:
                f.write("")

        # Create type stubs for all python files in subdirectory
        subprocess.run(f"pyright --createstub {subdirectory}")

        # Remove __init__.py and __init__.pyi file if it didn't exist before
        if not init_file_exists:
            os.remove(init_file_path)
            init_stub_file_path = os.path.join(
                base_dir, "typings", subdirectory, "__init__.pyi"
            )
            os.remove(init_stub_file_path)


def get_subdirectories(project_path):
    subdirectories = []
    base_dir = project_path.rsplit("/", 1)[0]
    for root, dirs, files in os.walk(project_path):
        contains_python_files = False
        for file in files:
            if file.endswith(".py"):
                contains_python_files = True
                break

        if contains_python_files:
            subdirectory = os.path.relpath(root, base_dir)
            subdirectories.append(subdirectory)

    return subdirectories
