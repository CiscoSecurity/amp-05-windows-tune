import zipfile
import os
import shutil
import re
from collections import Counter
import argparse
from pathlib import Path
from datetime import datetime


"""
Diag_analyzer.exe v2
Updated June 2025 by Sydney Jackson, Samiya Fyffe, Matthew Franks
"""

"""
Diag_analyzer.exe v1.04
22 June 2022
Written by Matthew Franks and Brandon Macer
"""


parser = argparse.ArgumentParser()
parser.add_argument(
    "-t",
    "--time",
    help='Time to start looking at logs (Must be in double quotes).  For example\n"Jan 22 00:00:01"',
    required=False,
)
parser.add_argument(
    "-i", "--infile", help="Location of the diagnostic file", required=False
)
parser.add_argument(
    "-d",
    "--directory",
    help="Directory location of the diagnostic files",
    required=False,
)
args = parser.parse_args()


def get_source(input_path=None):
    # 1. Use explicitly provided input path (highest priority)
    if input_path and os.path.isfile(input_path):
        return os.path.abspath(input_path)

    # 2. Use args.infile if available
    if hasattr(args, "infile") and args.infile:
        infile_path = os.path.join(os.curdir, args.infile)
        if os.path.isfile(infile_path):
            return os.path.abspath(infile_path)

    # 3. Use args.directory if it points to a file
    if hasattr(args, "directory") and args.directory:
        if os.path.isfile(args.directory):
            return os.path.abspath(args.directory)

    # 4. Search current directory for a matching file
    for file in os.listdir(os.curdir):
        if file.endswith((".7z", ".zip")):
            return os.path.abspath(os.path.join(os.curdir, file))

    # 5. Exit with error if nothing was found
    exit("No diagnostic file found or specified.")


def get_max_version(list_of_paths):
    max_version = [0, 0, 0]
    r = r"\d{1,2}\.\d{1,2}\.\d{1,2}.\d{1,5}"
    for path in list_of_paths:
        reg = re.findall(r, path)
        if reg:
            if list(map(lambda x: int(x), reg[0].split("."))) > max_version:
                max_version = list(map(lambda x: int(x), reg[0].split(".")))
    print(
        "Found latest version: "
        + ".".join(list(map(lambda x: str(x), max_version)))
        + "\n"
    )
    return ".".join(list(map(lambda x: str(x), max_version)))


def get_version(path):
    r = r"(\d{1,2}\.\d{1,2}\.\d{1,2}.\d{1,5}).*sfc\.exe.*"
    reg = re.findall(r, path)
    if reg:
        return reg[0]
    return "0.0.0"


def get_log_files_directory(source, output):
    files_7z = []
    for file in os.listdir(source):
        if file.endswith(".7z"):
            files_7z.append(file)
        elif file.endswith(".zip"):
            files_7z.append(file)
    log_files = []
    for file in files_7z:
        log_files.append(get_log_files(file, output))
    return log_files[0]


# Creates the output directory dependent upon version number
def get_log_files(source, output):
    print("Moving log files into the output directory.\n")
    try:
        with zipfile.ZipFile(source) as archive:
            namelist = []
            for x in archive.namelist():
                namelist.append(x)
            max_version = get_max_version(namelist)
            for f in archive.namelist():
                if get_version(f) == max_version:
                    fname = os.path.basename(f)
                    source = archive.open(f)
                    target = open(os.path.join(output, fname), "wb")
                    with source, target:
                        shutil.copyfileobj(source, target)
        archive.close()
        # Returns a list of file names that were just extracted to the output directory
        return os.listdir(output)
    except zipfile.BadZipFile:
        exit(f"Error: The file '{source}' is not a valid ZIP file.")


# Formats the output.
def print_info(data, name, source, count=100000):
    if args.directory:
        filename = "Directory-summary.txt"
    else:
        filename = f'{source.split(".")[0]}-summary.txt'
    with open(filename, "a") as f:
        print("\n-----------------------------------\nTop {} {}:\n".format(count, name))
        f.write("Top {} {}:\n".format(count, name))
        for i in data:
            print("{0:>8}".format(i[1]), i[0].rstrip())
            output = "{0:>8}".format(i[1]), i[0].rstrip()
            f.write("{} {}\n".format(str(output[0]), str(output[1])))
        print("\n\n")
        f.write("\n\n")


# Formats and writes the output to a specified file.
def print_info_to_file(data, name, results_dir, overwrite=False):
    # Always write to results/summary.txt
    file_name = os.path.join(results_dir, "-summary.txt")
    mode = "w" if overwrite else "a"
    with open(file_name, mode) as f:
        f.write("{}:\n".format(name))
        for i in data:
            output_line = "{0:>8}".format(i[1]), i[0].rstrip()
            f.write("{} {}\n".format(output_line[0], output_line[1]))
        f.write("\n\n")


def get_timestamped_results_dir():
    base_results_dir = Path.cwd() / "results"
    base_results_dir.mkdir(parents=True, exist_ok=True)

    # Replace colons with hyphens in the timestamp format
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    timestamped_dir = base_results_dir / timestamp  # Create a Path object
    timestamped_dir.mkdir(parents=True, exist_ok=True)

    return timestamped_dir


def main(source=None):
    source = get_source(source)

    # Get output folder name from the zip filename
    output_dir_name = os.path.splitext(os.path.basename(source))[0]

    # Create timestamped results directory
    results_dir = get_timestamped_results_dir()

    # Use the timestamped results directory as the base for output
    output = results_dir / output_dir_name
    output.mkdir(parents=True, exist_ok=True)  # Ensure output subfolder exists

    print(f"Logs will be extracted to: {output}")

    # Collect and extract logs into 'results'
    print("\nExtracting logs into 'results' directory...\n")
    try:
        if args.directory:
            log_files = get_log_files_directory(args.directory, output)
        else:
            log_files = get_log_files(source, output)
        print("Parsing the logs...\n")
    except OSError as e:
        exit(f"Log extraction failed: {str(e)}\n")

    data = []
    for log in log_files:
        if os.path.isdir(os.path.join(output, log)):
            continue  # Skip directories
        r = r"(\w{3} \d{1,2} \d\d:\d\d:\d\d).*Event::HandleCreation: START (\\\\\?\\[^\(]+)\(\\\\\?\\[^\)]+\), (\\\\\?\\.+)"
        with open(os.path.join(output, log), errors="ignore") as f:
            log_read = f.readlines()
        for line in log_read:
            if "Event::HandleCreation" in line:
                reg = re.findall(r, line)
                if reg:
                    data.append("{},{},{}\n".format(reg[0][0], reg[0][1], reg[0][2]))

    # Write results to results/summary.txt
    process_list = list(map(lambda x: x.split(",")[2], data))
    common_process = Counter(process_list).most_common(10)
    print_info_to_file(common_process, "Processes", results_dir, True)

    file_list = list(map(lambda x: x.split(",")[1], data))
    common_files = Counter(file_list).most_common(10)
    print_info_to_file(common_files, "Files", results_dir)

    extension_list = list(map(lambda x: x.split(",")[1], data))
    extension_list_scrubbed = []
    for i in extension_list:
        if "." in i.split("\\")[-1]:
            x = i.split(".")[-1]
            extension_list_scrubbed.append(x)
    common_extensions = Counter(extension_list_scrubbed).most_common(10)
    print_info_to_file(common_extensions, "Extensions", results_dir)

    path_list = list(map(lambda x: x.split(",")[1], data))
    path_list_scrubbed = []
    for i in path_list:
        path_only = i.split("\\")[:-1]
        path_only_merged = "\\".join(path_only)
        path_list_scrubbed.append(path_only_merged)
    common_paths = Counter(path_list_scrubbed).most_common(100)
    print_info_to_file(common_paths, "Paths", results_dir)

    return results_dir


if __name__ == "__main__":
    main()
