import zipfile
import os
import shutil
import re
from collections import Counter
import sys


'''
Diag_analyzer.exe v0.4

Usage:
    Diag_analyzer.exe
    #Will use the first diagnostic in the directory alphabetically
    or
    Diag_analyzer.exe Diagnostic_File.7z
    #Will use the diagnostic file specified

Diag_analyzer.exe will check the provided AMP diagnostic file for sfc.exe.log files.  
It will then create a directory with the diagnostic file name and store the log files outside of the .7z.
Next, it will parse the logs and determine the Top 10 Processes, Files, Extensions and Paths.
Finally, it will print that information to the screen and also to a {Diagnostic}-summary.txt file.
'''


def get_source():
    if len(sys.argv) == 2:
        source = os.path.join(os.curdir, sys.argv[1])
        return source

    elif len(sys.argv) > 2:
        print("Usage:\nDiag_analyzer.exe\nor\nDiag_analyzer.exe path/to/diagnostic")
        exit()

    else:
        for file in os.listdir(os.curdir):
            if file.endswith(".7z"):
                source = os.path.join(os.curdir, file)
                return source


def get_sfc_path():
    walk = list(os.walk(os.getcwd()))
    paths = []
    for i in walk:
        for j in i[-1]:
            paths.append("{}/{}".format(i[0], j).replace("\\", "/"))
    sfc_paths = list(filter(lambda x: "sfc.exe" in x and ".log" in x, paths))
    return sfc_paths


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


def get_log_files(source):
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


def print_info(data, name, count):
    with open("{}-summary.txt".format(source.split('.')[0]), "a") as f:
        print("Top {} {}:\n".format(count, name))
        f.write("Top {} {}:\n".format(count, name))
        for i in data:
            print('{0:>8}'.format(i[1]), i[0].rstrip())
            output = '{0:>8}'.format(i[1]), i[0].rstrip()
            f.write("{} {}\n".format(str(output[0]), str(output[1])))
        print("\n\n")
        f.write("\n\n")

def print_info_to_file(data, name):
    with open("{}-summary.txt".format(source.split('.')[0]), "a") as f:
        f.write("All {}:\n".format(name))
        for i in data:
            output = '{0:>8}'.format(i[1]), i[0].rstrip()
            f.write("{} {}\n".format(str(output[0]), str(output[1])))
        f.write("\n\n")

source = get_source().split('\\')[1]
output = "{}\\{}".format(os.getcwd(), source.split('.')[0])
try:
    if not os.path.exists(output):
        os.mkdir(output)
except OSError:
    print("Creation of the directory {} has failed.\n".format(output))
else:
    print("Successfully created the directory {}.\n".format(output))
log_files = get_log_files(source)
print("Parsing the logs.\n")
log_files2 = log_files[1:]
log_files2.append(log_files[0])
data = []
for log in log_files2:
    r = r'(\w{3} \d{1,2} \d\d:\d\d:\d\d).*Event::Handle.*\\\\\?\\(.*)\(\\\\\?\\.*\).*\\\\\?\\(.*)'
    with open(output+"/"+log, errors="ignore") as f:
        log_read = f.readlines()
    for line in log_read:
        if "Event::HandleCreation" in line:
            reg = re.findall(r, line)
            if reg:
                data.append("{},{},{}\n".format(reg[0][0], reg[0][1], reg[0][2]))

# Get Process information and print to screen and log
process_list = list(map(lambda x: x.split(',')[2], data))
common_process = Counter(process_list).most_common(10)
print_info(common_process, "Processes", 10)

# Get File information and print to screen and log
file_list = list(map(lambda x: x.split(',')[1], data))
common_files = Counter(file_list).most_common(10)
print_info(common_files, "Files", 10)

# Get Extension information and print to screen and log
extension_list = list(map(lambda x: x.split(',')[1], data))
extension_list_scrubbed = []
for i in extension_list:
    if '.' in i.split('\\')[-1]:
        x = i.split('.')[-1]
        extension_list_scrubbed.append(x)
common_extensions = Counter(extension_list_scrubbed).most_common(10)
print_info(common_extensions, "Extensions", 10)

# Get Path information and print to screen and log
path_list = list(map(lambda x: x.split(',')[1], data))
path_list_scrubbed = []
for i in path_list:
    path_only = i.split('\\')[:-1]
    path_only_merged = "\\".join(path_only)
    path_list_scrubbed.append(path_only_merged)
common_paths = Counter(path_list_scrubbed).most_common(100)
print_info(common_paths, "Paths", 100)

# Print all file scans to summary file
all_files = Counter(file_list).most_common(100000)
print_info_to_file(all_files, "Files")

#Hold screen open until Enter is pressed
while re.match(u'\u23CE', input("Press Enter to exit:\n")):
    break
