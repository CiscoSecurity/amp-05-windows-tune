import zipfile
import os
import shutil
import re
from collections import Counter
import sys
import argparse
import xml.etree.ElementTree as ET


'''
Diag_analyzer.exe v1.02
13 March 2019

Usage:
    Diag_analyzer.exe
    #Will use the first diagnostic in the directory alphabetically

    Diag_analyzer.exe -i Diagnostic_File.7z
    #Will use the diagnostic file specified

    Diag_analyzer.exe -i Diagnostic_File.7z -t "Jan 10 00:00:01"
    #Will use the diagnostic file specified and only return events from the date specified until the end of the session
    
    Diag_analyzer.exe -d .
    #Will process all diagnostics in the directory and provide summarized results.  Only works for current directory for now.

Diag_analyzer.exe will check the provided AMP diagnostic file for sfc.exe.log files and the policy.xml.
It will then create a directory with the diagnostic file name and store the log files outside of the .7z.
Next, it will parse the logs and determine the Top 10 Processes, Files, Extensions and Paths and 
print that information to the screen and also to a {Diagnostic}-summary.txt file.
Next, it will pull all exclusions from the policy.xml and sort them into categories for display.
If * leading exclusions are found, a warning will be displayed.

Written by Matthew Franks and Brandon Macer
'''

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--time",
                    help='Time to start looking at logs (Must be in double quotes).  For example\n"Jan 22 00:00:01"',
                    required=False)
parser.add_argument("-i", "--infile", help="Location of the diagnostic file", required=False)
parser.add_argument("-d", "--directory", help="Directory location of the diagnostic files", required=False)
parser.add_argument("-e", "--exclusions", help="List exclusions automatically with results.  For example,\n-e 1",
                    required=False)
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


def print_policy_info(excl_list, name, source):
    if len(excl_list) > 0:
        print("\n-----------------------------------\n")
        print(f'{name}\n')
        for exclusion in excl_list:
            if exclusion != '':
                print(exclusion)
        if args.directory:
            filename = "Directory-summary.txt"
        else:
            filename = f'{source.split(".")[0]}-summary.txt'
        with open(filename, "a") as f:
            f.write("\n-----------------------------------\n")
            f.write(f'{name}\n')
            for exclusion in excl_list:
                if exclusion != '':
                    f.write(f'{exclusion}\n')
            f.write("\n\n")


def parse_policy_xml(policy_xml, source, output):
    with open(output + "/" + policy_xml, errors="ignore") as f:
        tree = ET.parse(f)
        root = tree.getroot()
        path_exclusions = []
        extension_exclusions = []
        process_file_exclusions = []
        process_file_exclusions_with_children = []
        process_spp_exclusions = []
        process_spp_exclusions_with_children = []
        process_map_exclusions = []
        process_map_exclusions_with_children = []

        for child in root[2][0][1][0]:
            split = child.text.split('|')
            if split[-1].startswith('.*'):
                path_exclusions.append(split[-1])
            elif split[-1].startswith('.'):
                extension_exclusions.append(split[-1])
            else:
                path_exclusions.append(split[-1])
        for child in root[2][0][1][1]:
            split = child.text.split('|')
            if split[-2] == '0':
                process_file_exclusions.append(split[-3])
            elif split[-2] == '1':
                process_file_exclusions_with_children.append(split[-3])
            elif split[-2] == '4':
                process_spp_exclusions.append(split[-3])
            elif split[-2] == '12':
                process_spp_exclusions_with_children.append(split[-3])
            elif split[-2] == '16':
                process_map_exclusions.append(split[-3])
            elif split[-2] == '48':
                process_map_exclusions_with_children.append(split[-3])

        star = False
        for excl in path_exclusions:
            if excl.startswith('.*'):
                star = True
        cscvm37634 = '[WARNING] - Exclusions that start with * can lead to performance issues.\n \
                These should be converted to the Multi-drive exclusion type.\n \
                Please refer to CSCvm37634:\n \
                https://bst.cloudapps.cisco.com/bugsearch/bug/CSCvm37634/?reffering_site=dumpcr\n'
        if star:
            print(cscvm37634)
            if args.directory:
                filename = 'Directory-summary.txt'
            else:
                filename = f'{source.split(".")[0]}-summary.txt'
            with open(filename, "a") as f:
                f.write(cscvm37634)
                for excl in path_exclusions:
                    if excl.startswith('.*'):
                        f.write(f'{excl}\n')
                f.write('\n')
            for excl in path_exclusions:
                if excl.startswith('.*'):
                    print(excl)
                    path_exclusions.pop()
        if print_exclusions:
            print_policy_info(extension_exclusions, 'Extension Exclusions', source)
            print_policy_info(path_exclusions, 'File Exclusions', source)
            print_policy_info(process_file_exclusions, 'Process File Exclusions', source)
            print_policy_info(process_file_exclusions_with_children, 'Process File Exclusions with Children', source)
            print_policy_info(process_spp_exclusions, 'Process SPP Exclusions', source)
            print_policy_info(process_spp_exclusions_with_children, 'Process SPP Exclusions with Children', source)
            print_policy_info(process_map_exclusions, 'Process MAP Exclusions', source)
            print_policy_info(process_map_exclusions_with_children, 'Process MAP Exclusions with Children', source)


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
            if (get_version(f) == max_version) or (f.endswith('policy.xml')):
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
        filename = f'{source.split(".")[0]}'
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


def choose_show_exclusions():
    global print_exclusions
    if args.exclusions == '1':
        print_exclusions = True
    elif args.exclusions == '0':
        print_exclusions = False
    else:
        show_exclusions = input("Would you like to view the exclusions from your policy? [y/n]")
        if show_exclusions == 'y':
            print_exclusions = True
        elif show_exclusions == 'n':
            print_exclusions = False
        else:
            print("Your choice was not y or n.  Please try again.")
            choose_show_exclusions()


def main():
    try:
        source = get_source().split('\\')[1]
    except AttributeError:
        exit("No Diagnostic file found.")
    output = "{}\\{}".format(os.getcwd(), source.split('.')[0])
    try:
        if not os.path.exists(output):
            os.mkdir(output)
    except OSError:
        print("Creation of the directory {} has failed.\n".format(output))
    else:
        print("Successfully created the directory {}.\n".format(output))
    if args.directory:
        log_files = get_log_files_directory(args.directory, output)
    else:
        log_files = get_log_files(source, output)
    print("Parsing the logs.\n")
    # Put sfc.exe.log at the end of the list to maintain chronological order

    data = []
    choose_show_exclusions()
    for log in log_files:
        if log.endswith('policy.xml'):
            parse_policy_xml(log, source, output)
        else:
            r = r'(\w{3} \d{1,2} \d\d:\d\d:\d\d).*Event::Handle.*\\\\\?\\(.*)\(\\\\\?\\.*\).*\\\\\?\\(.*)'
            r_d = r'(\w{3} \d{1,2} \d\d:\d\d:\d\d)'
            with open(output+"/"+log, errors="ignore") as f:
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
    while re.match(u'\u23CE', input("Press Enter to exit:\n")):
        break

if __name__ == '__main__':
    main()
