[![Gitter chat](https://img.shields.io/badge/gitter-join%20chat-brightgreen.svg)](https://gitter.im/CiscoSecurity/AMP-for-Endpoints "Gitter chat")

### AMP for Endpoints Windows Tuning Tool:
Windows Endpoint tuning tool provides a quick view of top file and process scans occurring on a connector, designed to assist with performance tuning.

### Before using you must have the following:
Debug diagnostic file from the host in question

### Usage:
```
Diag_analyzer.exe 
	- will use the first diagnostic in the directory alphabetically
```	
or
```
Diag_analyzer.py Diagnostic_File.7z
	- will use the diagnostic file specified
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
