@echo off

SET /P version=<version

echo Removing old build and dist...
RMDIR /S /Q build
RMDIR /S /Q dist

echo Pyinstaller packing...
pyinstaller fastnote.spec --log-level WARN

echo Creating setup exe...
POWERSHELL -COMMAND "(GC windows\fastnote-setup.iss) -REPLACE '#define MyAppVersion \"1.0\"', '#define MyAppVersion \"%version%\"' | OUT-FILE dist\fastnote-setup.iss -Encoding ASCII"
ISCC dist\fastnote-setup.iss
DEL dist\fastnote-setup.iss

echo Completed.
