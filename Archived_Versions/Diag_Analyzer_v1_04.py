import zipfile
import os
import shutil
import re
from collections import Counter
import argparse
import logging
import socket
import struct


'''
Diag_analyzer.exe v1.04
22 June 2022

Usage:
    Diag_analyzer.exe
    #Will use the first diagnostic in the directory alphabetically

    Diag_analyzer.exe -i Diagnostic_File.7z
    #Will use the diagnostic file specified

    Diag_analyzer.exe -i Diagnostic_File.7z -t "Jan 10 00:00:01"
    #Will use the diagnostic file specified and only return events from the date specified until the end of the session

    Diag_analyzer.exe -d .
    #Will process all diagnostics in the directory and provide summarized results.  Only works for current directory for now.

Diag_analyzer.exe will check the provided AMP diagnostic file for sfc.exe.log files.
It will then create a directory with the diagnostic file name and store the log files outside of the .7z.
Next, it will parse the logs and determine the Top 10 Processes, Files, Extensions and Paths and
print that information to the screen and also to a {Diagnostic}-summary.txt file.

Written by Matthew Franks and Brandon Macer
'''

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--time",
                    help='Time to start looking at logs (Must be in double quotes).  For example\n"Jan 22 00:00:01"',
                    required=False)
parser.add_argument("-i", "--infile", help="Location of the diagnostic file", required=False)
parser.add_argument("-d", "--directory", help="Directory location of the diagnostic files", required=False)
args = parser.parse_args()


def get_source():
    if args.infile:
        source = os.path.join(os.curdir, args.infile)
        return source
    elif args.directory:
        source = args.directory
        return source
    else:
        for file in os.listdir(os.curdir):
            if file.endswith(".7z"):
                source = os.path.join(os.curdir, file)
                return source
            elif file.endswith(".zip"):
                source = os.path.join(os.curdir, file)
                return source
        exit("No diagnostic file found or specified.")


def get_max_version(list_of_paths):
    max_version = [0, 0, 0]
    r = r'\d{1,2}\.\d{1,2}\.\d{1,2}'
    for path in list_of_paths:
        reg = re.findall(r, path)
        if reg:
            if list(map(lambda x: int(x), reg[0].split("."))) > max_version:
                max_version = list(map(lambda x: int(x), reg[0].split(".")))
    return ".".join(list(map(lambda x: str(x), max_version)))


def get_version(path):
    r = r'(\d{1,2}\.\d{1,2}\.\d{1,2}).*sfc\.exe.*'
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


def get_log_files(source, output):
    print("Moving log files into the output directory.\n")
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
    return os.listdir(output)


def print_info(data, name, source, output, count=100000):
    if args.directory:
        filename = 'Directory-summary.txt'
    else:
        filename = f'{source.split(".")[0]}-summary.txt'
    with open(filename, "a") as f:
        print("\n-----------------------------------\nTop {} {}:\n".format(count, name))
        f.write("Top {} {}:\n".format(count, name))
        for i in data:
            print('{0:>8}'.format(i[1]), i[0].rstrip())
            output = '{0:>8}'.format(i[1]), i[0].rstrip()
            f.write("{} {}\n".format(str(output[0]), str(output[1])))
        print("\n\n")
        f.write("\n\n")


def print_info_to_file(data, name, source, output):
    if args.directory:
        file_name = 'Directory-summary.txt'
    else:
        file_name = f'{source.split(".")[0]}-summary.txt'
    with open(file_name, "a") as f:
        f.write("All {}:\n".format(name))
        for i in data:
            output = '{0:>8}'.format(i[1]), i[0].rstrip()
            f.write("{} {}\n".format(str(output[0]), str(output[1])))
        f.write("\n\n")


def get_top_paths(data, n_count=None):
    """
    Get a list of the top paths scanned by AMP.
    """
    path_list = list(map(lambda x: x.split(',')[1], data))
    path_list_scrubbed = []
    for i in path_list:
        path_only = i.split('\\')[:-1]
        path_only_merged = "\\".join(path_only)
        path_list_scrubbed.append(path_only_merged)
    c_count = Counter(path_list_scrubbed).most_common(n_count)
    return c_count


def get_top_exclusions(data, n_count=None):
    """
    Get count of top exclusions hit.
    """
    excluded_list = []
    for line in data:
        if "ExclusionCheck:" in line:
            reg = re.findall(r'ExclusionCheck: \\\\?\\.* is excluded', line)
            if reg:
                excluded_list.append(line.split(" ")[8])
    cnt = Counter(excluded_list)
    c_count = cnt.most_common(n_count)
    return c_count


def get_top_processes(data, n_count=None):
    """
    Get a list of the top system processes in terms of CPU usage.
    """
    process_list = list(map(lambda x: x.split(',')[2], data))
    c_count = Counter(process_list).most_common(n_count)
    return c_count


def get_top_extensions(data, n_count=None):
    """
    Get a list of the top extensions scanned by AMP.
    """
    extension_list = list(map(lambda x: x.split(',')[1], data))
    extension_list_scrubbed = []
    for i in extension_list:
        if '.' in i.split('\\')[-1]:
            x = i.split('.')[-1]
            extension_list_scrubbed.append(x)
    c_count = Counter(extension_list_scrubbed).most_common(n_count)
    return c_count


def convert_line(line):
    '''
    Conversion function.
    '''
    logging.debug("Starting convert_line")
    time, path, process = None, None, None
    regex_2 = r"(\w\w\w \d\d \d\d:\d\d:\d\d).*\\\\\?\\(.*)\\\\\?\\.*\\\\\?\\(.*)"
    reg = re.findall(regex_2, line)
    if reg:
        time, path, process = reg[0]
        logging.debug(f"time: {time}")
        logging.debug(f"path: {path}")
        logging.debug(f"process: {process}")
    return {
        "time": time,
        "path": path if path else None,  # Return None explicitly if path is missing
        "process": process
    }


def get_list_of_folders(file_path):
    r"""
    Takes a file path and returns list of folders involved
    Input: "C:\\Users\\mafranks\\Desktop\\file.txt"
    Output: ["C:\\Users", "C:\\Users\\mafranks", "C:\\Users\\mafranks\\Desktop",
    "C:\\Users\\mafranks\\Desktop\\file.txt"]
    """
    logging.debug("Starting get_list_of_folders")
    if not file_path:
        return []
    list_of_folders = []
    split_it = file_path.split("\\")
    for i in range(1, len(split_it)):
        list_of_folders.append("\\".join(split_it[0:i+1]))
    return list_of_folders


def parse_logs(log_files, output):
    """
    Parse the log files using the logic from data.py.
    """
    logging.debug("Starting parse_logs")
    data = []
    every_folder = []
    spero_count = 0
    ethos_count = 0
    quarantine_count = 0
    cloud_lookup_count = 0
    tetra_scan_count = 0
    excluded_count = 0
    cache_hit_count = 0
    malicious_hit_count = 0
    inner_file_count = 0
    excluded_list = []
    ip_list = []

    regex_1 = r"\\\\?\\.*\\\\?\\.*\\\\?\\.*"
    tetra_r = r"TetraEngineInterface::ScanFile\\[\\d{3,5}\\] lock acquired"

    for log in log_files:
        with open(os.path.join(output, log), errors="ignore") as f:
            for line in f:
                if "Event::Handle" in line:
                    logging.debug("Found Event::Handle")
                    reg = re.findall(regex_1, line)
                    if reg:
                        converted = convert_line(reg[0])
                        logging.debug(f"converted: {converted}")
                        data.append(converted)
                        to_add = get_list_of_folders(converted["path"])[:-1]
                        logging.debug(f"Extending every_folder with: {to_add}")
                        every_folder.extend(to_add)
                    if "EVENT_INNER_FILE_SCAN start" in line:
                        inner_file_count += 1
                elif "GetSperoHash SPERO fingerprint: status: 1" in line:
                    spero_count += 1
                    logging.debug(f"found SPERO: {spero_count}")
                elif "imn::CEventManager::PublishEvent: publishing type=553648143" in line:
                    quarantine_count += 1
                    logging.debug(f"found Quarantine: {quarantine_count}")
                elif "Query::LookupExecute: attempting lookup with cloud" in line:
                    cloud_lookup_count += 1
                    logging.debug(f"found lookup cloud: true: {cloud_lookup_count}")
                elif "lock acquired" in line:
                    logging.debug("found lock acquired")
                    reg = re.findall(tetra_r, line)
                    if reg:
                        tetra_scan_count += 1
                        logging.debug(f"found Tetra ScanFile lock: {tetra_scan_count}")
                elif "ExclusionCheck: responding: is excluded" in line:
                    excluded_count += 1
                    logging.debug(f"found is excluded: {excluded_count}")
                elif "ExclusionCheck:" in line:
                    reg = re.findall(r'ExclusionCheck: \\\\?\\.* is excluded', line)
                    if reg:
                        excluded_list.append(line.split(" ")[8])
                        excluded_count += 1
                elif "Exclusion::IsExcluded: result: 1 for" in line:
                    excluded_list.append(line.split("result: 1 for ")[1].split(",")[0])
                    excluded_count += 1
                elif "Exclusion::IsExcluded: result: 1 from cache" in line:
                    excluded_list.append(line.split("result: 1 from cache for ")[1])
                    excluded_count += 1
                elif "Cache::Get: age" in line:
                    cache_hit_count += 1
                    logging.debug(f"found Cache::Get: age {cache_hit_count}")
                elif "calculating ETHOS hash" in line:
                    ethos_count += 1
                    logging.debug(f"found ETHOS hash {ethos_count}")
                elif "NFMMemCache::Get: rip" in line:
                    reg = re.findall(r'NFMMemCache::Get: rip: ([\\d]*)', line)
                    if reg and reg[0]:  # Ensure reg[0] is not empty
                        try:
                            converted = socket.inet_ntoa(struct.pack('!L', int(reg[0])))
                            ip_list.append(".".join(reversed(converted.split("."))))
                        except ValueError:
                            logging.warning(f"Invalid IP address value: {reg[0]}")
                if "disp 3" in line:
                    malicious_hit_count += 1
                    logging.debug(f"found disp 3 {malicious_hit_count}")

    return {
        "data": data,
        "every_folder": every_folder,
        "spero_count": spero_count,
        "ethos_count": ethos_count,
        "quarantine_count": quarantine_count,
        "cloud_lookup_count": cloud_lookup_count,
        "tetra_scan_count": tetra_scan_count,
        "excluded_count": excluded_count,
        "cache_hit_count": cache_hit_count,
        "malicious_hit_count": malicious_hit_count,
        "inner_file_count": inner_file_count,
        "excluded_list": excluded_list,
        "ip_list": ip_list
    }


def main():
    try:
        source = get_source().split(os.sep)[1]
    except AttributeError:
        exit("No Diagnostic file found.")
    output = os.path.join(os.getcwd(), source.split('.')[0])
    print("\nCreating directory\n")
    try:
        if not os.path.exists(output):
            os.mkdir(output)
            print("Successfully created the directory '{}'.\n".format(output))
        else:
            print(f"{output} directory already exists.\n")
    except OSError:
        exit("Creation of the directory {} has failed.\n".format(output))
    if args.directory:
        log_files = get_log_files_directory(args.directory, output)
    else:
        log_files = get_log_files(source, output)
    print("Parsing the logs.\n")

    # Use the new parse_logs function
    parsed_data = parse_logs(log_files, output)

    # Process and print the parsed data
    common_paths = get_top_paths(parsed_data["data"], 10)
    print_info(common_paths, "Paths", source, output, 10)

    common_exclusions = get_top_exclusions(parsed_data["data"], 10)
    print_info(common_exclusions, "Exclusions", source, output, 10)

    common_processes = get_top_processes(parsed_data["data"], 10)
    print_info(common_processes, "Processes", source, output, 10)

    common_extensions = get_top_extensions(parsed_data["data"], 10)
    print_info(common_extensions, "Extensions", source, output, 10)

    if args.directory:
        filename = 'Directory-summary.txt'
    else:
        filename = f'{source.split(".")[0]}-summary.txt'
    while re.match(u'\u23CE', input(f"Logs written to {filename}.\n\nPress Enter to exit:\n")):
        break


if __name__ == '__main__':
    main()