@echo off

rem In this script we assume that you have installed NSIS, gtk-dev,
rem mingw (make and cc), Python2.5, pygtk, pygobject, pycairo,
rem py2exe, scapy win32 and rem relative dependencies
rem (http://trac.secdev.org/scapy/wiki/WindowsInstallationGuide)
rem respectively in:
rem C:\Program files\NSIS, C:\GTK, C:\Mingw, C:\python25

rem We also assume that you have PATH setted as:
rem C:\gtk\bin;C:\mingw\bin;c:\python25;$PATH

echo Setting installation variables...
set PM_DOCKING=1
set PythonEXE=C:\Python25\python.exe
set PMOrig=.
set PMDir=C:\PMTemp
set DistDir=%PMDir%\dist
set GTKDir=C:\GTK
set WinInstallDir=%PMDir%\scripts\windows
set Output=%PMDir%\win_install.log
set MakeNSIS="C:\Program Files\NSIS\makensis.exe"

echo Writing output to %Output%
rd %Output% /S /Q

echo Removing old compilation...
rd %PMDir% /S /Q

echo Creating a temp directory for compilation...
mkdir %PMDir%

echo Copying trunk to the temp dir...
xcopy %PMOrig%\*.* %PMDir% /E /S /C /Y /V /I >> %Output%
xcopy %PMOrig%\scripts\windows\setup.nsi %PMDir% /E /S /C /Y /V /I >> %Output%

echo Creating dist and dist\share directories...
mkdir %DistDir%\share
mkdir %DistDir%\share\themes
mkdir %DistDir%\share\themes\Default
mkdir %DistDir%\share\themes\MS-Windows

echo Copying GTK's share to dist directory...
xcopy %GTKDir%\share\themes\Default\*.* %DistDir%\share\themes\Default /S /Y >> %Output%
xcopy %GTKDir%\share\themes\MS-Windows\*.* %DistDir%\share\themes\MS-Windows /S /Y >> %Output%
xcopy %GTKDir%\bin\*.dll %DistDir% /Y /S >> %Output%

echo Copying setup.py...
xcopy %WinInstallDir%\setup.py %PMDir% /Y

echo Compiling PacketManipulator using py2exe...
cd %PMDir%
%PythonEXE% setup.py py2exe

echo Copying some more GTK files to dist directory...
xcopy %GTKDir%\lib %DistDir%\lib /S /I >> %Output%
xcopy %GTKDir%\etc %DistDir%\etc /S /I >> %Output%

echo Removing the build directory...
rd %PMDir%\build /s /q >> %Output%

echo .
echo Creating installer...
%MakeNSIS% /P5 /V4 /NOCD %WinInstallDir%\setup.nsi

cd %PMOrig%
echo Done!
