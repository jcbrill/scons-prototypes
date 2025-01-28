@rem optional first argument: test directory

@setlocal

:: set PYEXE to fully qualified python executable
:: set SCONS_ROOT to scons root directory

@set "SCRIPT_ROOT=%~dp0"
@if "%SCRIPT_ROOT:~-1%" == "\" set "SCRIPT_ROOT=%SCRIPT_ROOT:~0,-1%"

@if "%SCONS_ROOT%" == "" @set "SCONS_ROOT=%SCRIPT_ROOT%\..\..\scons-master"

@if "%SCONS_SITEDIR%" == "" @set "SCONS_SITEDIR=%SCRIPT_ROOT%\..\site-scons"

@if "%1"=="" @goto default-scons
@set "TEST_ROOT=%1"
@goto scons
:default-scons
@set "TEST_ROOT=%SCRIPT_ROOT%\ScannerTest"
@goto scons

:scons

@if NOT "%PYEXE%" == "" @goto :run

@if EXIST e:\python @goto edrive
@call z:\python\python-embed 3.7
@goto run
:edrive
@call e:\python\python-embed 3.7
@goto run

:run

@pushd "%TEST_ROOT%"

@if exist .sconsign.dblite @del /Q .sconsign.dblite

@echo --- scons:beg ---
@"%PYEXE%" "%SCONS_ROOT%\scripts\scons.py" -Qn --site-dir="%SCONS_SITEDIR%"
@echo --- scons:end ---

@if exist .sconsign.dblite @del /Q .sconsign.dblite

@popd

@endlocal
