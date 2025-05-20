import zipfile
import os
import shutil
import re
from collections import Counter
import argparse


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
    r = r'\d{1,2}\.\d{1,2}\.\d{1,2}.\d{1,5}'
    for path in list_of_paths:
        reg = re.findall(r, path)
        if reg:
            if list(map(lambda x: int(x), reg[0].split("."))) > max_version:
                max_version = list(map(lambda x: int(x), reg[0].split(".")))
    print("Found latest version: " + ".".join(list(map(lambda x: str(x), max_version))) + "\n")
    return ".".join(list(map(lambda x: str(x), max_version)))


def get_version(path):
    r = r'(\d{1,2}\.\d{1,2}\.\d{1,2}.\d{1,5}).*sfc\.exe.*'
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


def main():
    try:
        source = get_source()
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
    # Put sfc.exe.log at the end of the list to maintain chronological order

    data = []
    for log in log_files:
        if os.path.isdir(os.path.join(output, log)):
            continue  # Skip directories
        r = r'(\w{3} \d{1,2} \d\d:\d\d:\d\d).*Event::Handle.*\\\\\?\\(.*)\\(\\\\\?\\.*\\).*\\\\\?\\(.*)'
        r_d = r'(\w{3} \d{1,2} \d\d:\d\d:\d\d)'
        with open(os.path.join(output, log), errors="ignore") as f:
            log_read = f.readlines()
        for line in log_read:
            if "Event::HandleCreation" in line:
                if args.time:
                    if re.findall(r_d, line)[0] > args.time:
                        reg = re.findall(r, line)
                        if reg:
                            data.append("{},{},{}\n".format(reg[0][0], reg[0][1], reg[0][2]))
                else:
                    reg = re.findall(r, line)
                    if reg:
                        data.append("{},{},{}\n".format(reg[0][0], reg[0][1], reg[0][2]))


    # Get Process information and print to screen and log
    process_list = list(map(lambda x: x.split(',')[2], data))
    common_process = Counter(process_list).most_common(10)
    print_info(common_process, "Processes", source, output, 10)

    # Get File information and print to screen and log
    file_list = list(map(lambda x: x.split(',')[1], data))
    common_files = Counter(file_list).most_common(10)
    print_info(common_files, "Files", source, output, 10)

    # Get Extension information and print to screen and log
    extension_list = list(map(lambda x: x.split(',')[1], data))
    extension_list_scrubbed = []
    for i in extension_list:
        if '.' in i.split('\\')[-1]:
            x = i.split('.')[-1]
            extension_list_scrubbed.append(x)
    common_extensions = Counter(extension_list_scrubbed).most_common(10)
    print_info(common_extensions, "Extensions", source, output, 10)

    # Get Path information and print to screen and log
    path_list = list(map(lambda x: x.split(',')[1], data))
    path_list_scrubbed = []
    for i in path_list:
        path_only = i.split('\\')[:-1]
        path_only_merged = "\\".join(path_only)
        path_list_scrubbed.append(path_only_merged)
    common_paths = Counter(path_list_scrubbed).most_common(100)
    print_info(common_paths, "Paths", source, output, 100)

    # Print all file scans to summary file
    all_files = Counter(file_list).most_common(100000)
    print_info_to_file(all_files, "Files", source, output)

    #Hold screen open until Enter is pressed
    if args.directory:
        filename = 'Directory-summary.txt'
    else:
        filename = f'{source.split(".")[0]}-summary.txt'

if __name__ == '__main__':
    main()
