'''
Diag_analyzer.exe v1.03b
12 November 2019

Usage:
    Diag_analyzer.exe
    #Will use the first diagnostic in the directory alphabetically

    Diag_analyzer.exe -i Diagnostic_File.7z
    #Will use the diagnostic file specified

    Diag_analyzer.exe -i Diagnostic_File.7z -t "Jan 10 00:00:01"
    #Will use the diagnostic file specified and only return events from the
    date specified until the end of the session

    Diag_analyzer.exe -d .
    #Will process all diagnostics in the directory and provide summarized
    results.  Only works for current directory for now.

    Diag_analyzer.exe -c .
    #Will convert paths from the log file into CSIDL format where possible


Diag_analyzer.exe will check the provided AMP diagnostic file for sfc.exe.log
files and the policy.xml. It will then create a directory with the diagnostic
file name and store the log files outside of the .7z.

Next, it will parse the logs and determine the Top 10 Processes, Files,
Extensions and Paths and print that information to the screen and also to a
{Diagnostic}-summary.txt file.

Next, it will pull all exclusions from the policy.xml and sort them into
categories for display. If * leading exclusions are found, a warning will be
displayed.

Written by Matthew Franks and Brandon Macer
'''

import zipfile
import os
import shutil
import re
from collections import Counter
import sys
import argparse
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--time",
                    help='Time to start looking at logs (Must be in double quotes).  " \
                    "For example\n"Jan 22 00:00:01"',
                    required=False)
parser.add_argument("-i", "--infile",
                    help="Location of the diagnostic file",
                    required=False)
parser.add_argument("-d", "--directory",
                    help="Directory location of the diagnostic files",
                    required=False)
parser.add_argument("-e", "--exclusions",
                    help="List exclusions automatically with results. For example,\n-e 1",
                    required=False)
### START ADDED CODE - for converting log file paths to CSIDL
parser.add_argument("-c", "--csidl",
                    help="Convert file paths into CSIDL format (does not apply to policy.xml)" \
                        "0=False, 1=True",
                    required=False)
### END ADDED CODE
args = parser.parse_args()


def get_source():
    '''
    Return the source if specified as a directory or a file. If the source
    is not specified, check the current directory for archive files.
    '''
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
        sys.exit("No diagnostic file found or specified.")


def get_max_version(list_of_paths):
    '''
    Using the results of 'get_version' determine the largest version number.
    '''
    max_version = [0, 0, 0]
    version_regex = r'\d{1,2}\.\d{1,2}\.\d{1,2}'
    for path in list_of_paths:
        reg = re.findall(version_regex, path)
        if reg:
            if list(map(lambda x: int(x), reg[0].split("."))) > max_version:
                max_version = list(map(lambda x: int(x), reg[0].split(".")))
    return ".".join(list(map(lambda x: str(x), max_version)))


def get_version(path):
    '''
    Get a list of the connector version folders from the archive.
    '''
    executable_path_regex = r'(\d{1,2}\.\d{1,2}\.\d{1,2}).*sfc\.exe.*'
    reg = re.findall(executable_path_regex, path)
    if reg:
        return reg[0]
    return "0.0.0"


def print_policy_info(excl_list, name, source):
    '''
    Print out the policy information.
    '''
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
        with open(filename, "a") as file:
            file.write("\n-----------------------------------\n")
            file.write(f'{name}\n')
            for exclusion in excl_list:
                if exclusion != '':
                    file.write(f'{exclusion}\n')
            file.write("\n\n")


def parse_policy_xml(policy_xml, source, output):
    '''
    Parse the policy.xml file.
    '''
    with open(output + "/" + policy_xml, errors="ignore") as file:
        tree = ET.parse(file)
        root = tree.getroot()
        obj_location = excl_location = 0

        if root[2].tag[-6:] == 'Object':
            obj_location = 2
            excl_location = 1

            ### START ADDED CODE - required for Orbital entry in policy.xml
            if root[obj_location][0][excl_location].tag[-7:] == 'orbital':
                excl_location = 2
            ### END ADDED CODE

        elif root[3].tag[-6:] == 'Object':
            obj_location = 3
            excl_location = 4

        if obj_location > 0:
            path_exclusions = []
            extension_exclusions = []
            process_file_exclusions = []
            process_file_exclusions_with_children = []
            process_spp_exclusions = []
            process_spp_exclusions_with_children = []
            process_map_exclusions = []
            process_map_exclusions_with_children = []

            for child in root[obj_location][0][excl_location][0]:
                split = child.text.split('|')
                if split[-1].startswith('.*'):
                    path_exclusions.append(split[-1])
                elif split[-1].startswith('.'):
                    extension_exclusions.append(split[-1])
                else:
                    path_exclusions.append(split[-1])
            star = False
            cscvm37634 = '[WARNING] - Exclusions that start with * can lead to ' \
                'performance issues.\nThese should be converted to the Multi-drive ' \
                'exclusion type.\nPlease refer to CSCvm37634:\n'\
                'https://bst.cloudapps.cisco.com/bugsearch/bug/CSCvm37634/?reffering_site=dumpcr\n'

            try:
                for child in root[obj_location][0][excl_location][1]:
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

                for excl in path_exclusions:
                    if excl.startswith('.*'):
                        star = True

            except IndexError:
                print("\nNo process exclusions found.\n")

            if star:
                print(cscvm37634)
                if args.directory:
                    filename = 'Directory-summary.txt'
                else:
                    filename = f'{source.split(".")[0]}-summary.txt'
                with open(filename, "a") as file:
                    file.write(cscvm37634)
                    for excl in path_exclusions:
                        if excl.startswith('.*'):
                            file.write(f'{excl}\n')
                    file.write('\n')
                for excl in path_exclusions:
                    if excl.startswith('.*'):
                        print(excl)
                        path_exclusions.pop()
            if print_exclusions:
                print_policy_info(extension_exclusions, 'Extension Exclusions', source)
                print_policy_info(path_exclusions, 'File Exclusions', source)
                print_policy_info(process_file_exclusions, 'Process File Exclusions', source)
                print_policy_info(process_file_exclusions_with_children, 'Process File \
                                  Exclusions with Children', source)
                print_policy_info(process_spp_exclusions, 'Process SPP Exclusions', source)
                print_policy_info(process_spp_exclusions_with_children, 'Process SPP \
                                  Exclusions with Children', source)
                print_policy_info(process_map_exclusions, 'Process MAP Exclusions', source)
                print_policy_info(process_map_exclusions_with_children, 'Process MAP Exclusions \
                                  with Children', source)
        else:
            print("Unable to properly read policy.xml.  Skipping Exclusion check.")


def get_log_files_directory(source, output):
    '''
    If the -d agrument is used, create a list of archive files and pass each
    file to the 'get_log_files' function for log file extraction.
    '''
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
    '''
    Extract the log files for the archive file specified.
    '''
    print("Moving log files into the output directory.\n")
    with zipfile.ZipFile(source) as archive:
        namelist = []
        for arc_name in archive.namelist():
            namelist.append(arc_name)
        max_version = get_max_version(namelist)
        for file_name in archive.namelist():
            if (get_version(file_name) == max_version) or (file_name.endswith('policy.xml')):
                fname = os.path.basename(file_name)
                source = archive.open(file_name)
                target = open(os.path.join(output, fname), "wb")
                with source, target:
                    shutil.copyfileobj(source, target)
    archive.close()
    return os.listdir(output)


def print_info(data, name, source, output, count=100000):
    '''
    Create a results file for the summary information per connector
    '''
    if args.directory:
        filename = 'Directory-summary.txt'
    else:
        filename = f'{source.split(".")[0]}-summary.txt'
    with open(filename, "a") as file:
        print("\n-----------------------------------\nTop {} {}:\n".format(count, name))
        file.write("Top {} {}:\n".format(count, name))
        for i in data:
            print('{0:>8}'.format(i[1]), i[0].rstrip())
            output = '{0:>8}'.format(i[1]), i[0].rstrip()
            file.write("{} {}\n".format(str(output[0]), str(output[1])))
        print("\n\n")
        file.write("\n\n")


def print_info_to_file(data, name, source, output):
    '''
    If the -d argument was used, append summary results for all connectors
    '''
    if args.directory:
        file_name = 'Directory-summary.txt'
    else:
        file_name = f'{source.split(".")[0]}-summary.txt'
    with open(file_name, "a") as file:
        file.write("All {}:\n".format(name))
        for i in data:
            output = '{0:>8}'.format(i[1]), i[0].rstrip()
            file.write("{} {}\n".format(str(output[0]), str(output[1])))
        file.write("\n\n")


def choose_show_exclusions():
    '''
    Command prompt interaction if the -e argument is not used.
    '''
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


### START ADDED CODE
def convert_to_csidl(entry):
    '''
    Looks at results and parses the path information to CSIDL format
    '''
    entry = re.sub('^.:\\\\ProgramData\\\\', 'CSIDL_COMMON_APPDATA\\\\',
                   entry, flags=re.IGNORECASE)
    entry = re.sub('^.:\\\\Program Files \\(x86\\)\\\\', 'CSIDL_PROGRAM_FILESX86\\\\',
                   entry, flags=re.IGNORECASE)
    entry = re.sub('^.:\\\\Program Files\\\\', 'CSIDL_PROGRAM_FILES\\\\',
                   entry, flags=re.IGNORECASE)
    entry = re.sub('^.:\\\\Users\\\\.+?\\\\AppData\\\\Local\\\\', 'CSIDL_LOCAL_APPDATA\\\\',
                   entry, flags=re.IGNORECASE)
    entry = re.sub('^.:\\\\Users\\\\.+?\\\\AppData\\\\Roaming\\\\', 'CSIDL_APPDATA\\\\',
                   entry, flags=re.IGNORECASE)
    entry = re.sub('^.:\\\\Users\\\\.+?\\\\Desktop\\\\', 'CSIDL_DESKTOPDIRECTORY\\\\',
                   entry, flags=re.IGNORECASE)
    entry = re.sub('^.:\\\\Users\\\\.+?\\\\', 'CSIDL_PROFILE\\\\',
                   entry, flags=re.IGNORECASE)
    entry = re.sub('^.:\\\\Windows\\\\System32\\\\', 'CSIDL_SYSTEM\\\\',
                   entry, flags=re.IGNORECASE)
    entry = re.sub('^.:\\\\Windows\\\\', 'CSIDL_WINDOWS\\\\',
                   entry, flags=re.IGNORECASE)
    entry = re.sub('^.:\\\\Users\\\\.+?\\\\', 'CSIDL_PROFILE\\\\',
                   entry, flags=re.IGNORECASE)
    return entry
### END ADDED CODE


def main():
    '''
    Main function for this script.
    '''
    try:
        source = get_source().split('\\')[1]
    except AttributeError:
        sys.exit("No Diagnostic file found.")
    output = "{}\\{}".format(os.getcwd(), source.split('.')[0])
    print("\nCreating directory\n")
    try:
        if not os.path.exists(output):
            os.mkdir(output)
            print("Successfully created the directory {}.\n".format(output))
        else:
            print(f"{output} directory already exists.\n")
    except OSError:
        sys.exit("Creation of the directory {} has failed.\n".format(output))
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
            event_regex = r'(\w{3} \d{1,2} \d\d:\d\d:\d\d).*Event::Handle.*\\\\\?\\(.*)\(\\\\\?\\.*\).*\\\\\?\\(.*)'
            r_d = r'(\w{3} \d{1,2} \d\d:\d\d:\d\d)'
            with open(output+"/"+log, errors="ignore") as file:
                log_read = file.readlines()
            for line in log_read:
                if "Event::HandleCreation" in line:
                    if args.time:
                        if re.findall(r_d, line)[0] > args.time:
                            reg = re.findall(event_regex, line)
                            if reg:
                                ### START ADDED CODE
                                if args.csidl == '1':
                                    item_a = reg[0][0]
                                    item_b = str(reg[0][1])
                                    item_c = str(reg[0][2])
                                    item_b = convert_to_csidl(item_b)
                                    item_c = convert_to_csidl(item_c)
                                    data.append("{},{},{}\n".format(item_a, item_b, item_c))
                                else:
                                ### END ADDED CODE
                                    data.append("{},{},{}\n".format(reg[0][0], reg[0][1], reg[0][2]))
                    else:
                        reg = re.findall(event_regex, line)
                        if reg:
                             ### START ADDED CODE
                            if args.csidl == '1':
                                item_a = reg[0][0]
                                item_b = str(reg[0][1])
                                item_c = str(reg[0][2])
                                item_b = convert_to_csidl(item_b)
                                item_c = convert_to_csidl(item_c)
                                data.append("{},{},{}\n".format(item_a, item_b, item_c))
                            else:
                            ### END ADDED CODE
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
            extension = i.split('.')[-1]
            extension_list_scrubbed.append(extension)
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
    while re.match(u'\u23CE', input(f"Logs written to {filename}.\n\nPress Enter to exit:\n")):
        break

if __name__ == '__main__':
    main()
