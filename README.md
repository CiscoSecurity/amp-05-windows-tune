[![Gitter chat](https://img.shields.io/badge/gitter-join%20chat-brightgreen.svg)](https://gitter.im/CiscoSecurity/AMP-for-Endpoints "Gitter chat")

### AMP for Endpoints Windows Tuning Tool:
Windows Endpoint tuning tool provides a quick view of top file and process scans occurring on a connector, designed to assist with performance tuning.

### Before using you must have the following:
Debug diagnostic file from the host in question

### Usage:
Place PE in the directory where the debug diagnostic file is to run the tool.
```
Diag_analyzer.exe 
	- will use the first diagnostic in the directory alphabetically
```	
OR
```
Additional flags:
 -t "<time>": specify time for log inclusion

 time format: 3_letter_month 2_digit_day 24hour:minute:second i.e. Jan 01 01:01:01 is January 1st at 1:01:01AM
 
 Example: Diag_analyzer.exe -t "Jan 01 01:01:01"
 Results will be based on the logs starting at specified time until end of logs
 
 
 -i : specify diagnostic file
 Example: Diag_analyzer.exe -i Cisco_AMP_Diag.7z
 Results will be based on the specified diagnostic file
 
 
 Combo results
 Example: Diag_analyzer.exe -i Cisco_AMP_diah.7z -t "Jan 01 01:01:01"
 Results: Specified diagnostic file will be analyzed from Jan 1st, 01:01:01 AM to current
```
Diag_analyzer.exe will check the provided AMP diagnostic file for sfc.exe.log files.  
It will then create a directory with the diagnostic file name and store the log files outside of the .7z, in the parent directory of the diagnostic.
Next, it will parse the logs and determine the Top 10 Processes, Files, Extensions and Paths.
Finally, it will print that information to the screen and also to a {Diagnostic}-summary.txt file.

### Example script output:  
```
Top 10 Processes:
     423 C:\Program Files (x86)\Google\Chrome\Application\chrome.exe
     308 C:\Windows\explorer.exe
     168 C:\Users\testuser\AppData\Local\Programs\Python\Python37-32\python.exe
     150 C:\Users\testuser\AppData\Local\Packages\CanonicalGroupLimited.UbuntuonWindows_79rhkp1fndgsc\LocalState\rootfs\usr\bin\python3.6
     112 C:\Program Files\JetBrains\PyCharm Community Edition 2018.3\bin\pycharm64.exe
      83 C:\Windows\System32\wbem\WmiPrvSE.exe
      64 C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe
      55 C:\Program Files (x86)\Atlassian\HipChat4\HipChat.exe
      29 C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE
      25 C:\Windows\System32\svchost.exe


Top 10 Files:
      22 C:\Windows\CCM\clientstate.dat
      21 C:\Windows\System32\config\systemprofile\AppData\Local\Microsoft\Windows\PowerShell\StartupProfileData-NonInteractive
      13 C:\Users\testuser\.PyCharmCE2018.3\system\caches\records.dat
      10 C:\ProgramData\NVIDIA Corporation\Drs\nvAppTimestamps
      10 C:\Users\testuser\.PyCharmCE2018.3\system\caches\contentHashes.dat.keystream
      10 C:\Users\testuser\.PyCharmCE2018.3\system\caches\contentHashes.dat_i
      10 C:\Users\testuser\.PyCharmCE2018.3\system\caches\contentHashes.dat
       9 C:\Users\testuser\.PyCharmCE2018.3\config\options\recentProjectDirectories.xml
       9 C:\Users\testuser\AppData\Local\Temp\decompress.py\.idea\workspace.xml___jb_tmp___
       8 C:\Windows\CCM\StateMessageStore.sdf


Top 10 Extensions:
     372 txt
     233 tmp
      81 gz
      56 dat
      53 vbs
      52 xml
      50 db
      45 ps1
      39 tar
      22 psm1


Top 100 Paths:
     306 C:\Users\testuser\Desktop\TEST\decompress
     293 C:\$Recycle.Bin\S-1-5-21-1708537768-1303643608-725345543-9394300
     168 C:\Users\testuser\AppData\Local\Google\Chrome\User Data\Default\Cache
     167 C:\Users\testuser\AppData\Local\Google\Chrome\User Data\Default
      75 C:\Windows\CCM\SystemTemp
      46 C:\Windows\Temp
      ...
      
All Files:
      22 C:\Windows\CCM\clientstate.dat
      21 C:\Windows\System32\config\systemprofile\AppData\Local\Microsoft\Windows\PowerShell\StartupProfileData-NonInteractive
```
```


###Beta Version
The Beta version adds a -d (directory) option allowing you to process results for all diagnostics in the directory and return the combines results.  This could be useful for determining appropriate exclusions for an entire department at once.

```
Diag_analyzer_beta.exe -d .
	- Will process all AMP diagnostics in the directory with the execuatable
	
```
