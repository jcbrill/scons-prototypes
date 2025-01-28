@setlocal

@set "SCRIPT_ROOT=%~dp0"
@if "%SCRIPT_ROOT:~-1%" == "\" set "SCRIPT_ROOT=%SCRIPT_ROOT:~0,-1%"

@if "%SCONS_ROOT%" == "" @set "SCONS_ROOT=%SCRIPT_ROOT%\..\..\scons-master"

@if "%SCONS_SITEDIR%" == "" @set "SCONS_SITEDIR=%SCRIPT_ROOT%\..\site-scons"

@set "TEST_ROOT=%SCRIPT_ROOT%\IssueTest"

@set _SCONS_SCANNER=CPreProcessorScanner
@set _SCONS_MSVC_COMPILER=

@if "%1" == "" @goto :python
@set _SCONS_SCANNER=%1

@if NOT "%2" == "--msvc-compiler" @goto :python
@set _SCONS_MSVC_COMPILER=%2

:python

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

@echo.
@echo --- scons:deps:beg ---
@"%PYEXE%" "%SCONS_ROOT%\scripts\scons.py" --site-dir="%SCONS_SITEDIR%" -Qn --scanner-deps %_SCONS_MSVC_COMPILER% --scanner=%_SCONS_SCANNER% --expected-map="{'main.c': []}"
@echo --- scons:deps:end ---
@echo.
@echo --- scons:build:beg ---
@"%PYEXE%" "%SCONS_ROOT%\scripts\scons.py" --site-dir="%SCONS_SITEDIR%" -Qn --tree=all %_SCONS_MSVC_COMPILER% --scanner=%_SCONS_SCANNER%
@echo --- scons:build:end ---
@echo.
@echo --- scons:clean:beg ---
@"%PYEXE%" "%SCONS_ROOT%\scripts\scons.py" --site-dir="%SCONS_SITEDIR%" -Qn --clean %_SCONS_MSVC_COMPILER% --scanner=%_SCONS_SCANNER%
@echo --- scons:clean:end ---

@echo.
@echo --- scons:deps:beg ---
@"%PYEXE%" "%SCONS_ROOT%\scripts\scons.py" --site-dir="%SCONS_SITEDIR%" -Qn --scanner-deps %_SCONS_MSVC_COMPILER% --scanner=%_SCONS_SCANNER% --FEATURE_A_ENABLED= --expected-map="{'main.c': []}"
@echo --- scons:deps:end ---
@echo.
@echo --- scons:build:beg ---
@"%PYEXE%" "%SCONS_ROOT%\scripts\scons.py" --site-dir="%SCONS_SITEDIR%" -Qn --tree=all %_SCONS_MSVC_COMPILER% --scanner=%_SCONS_SCANNER% --FEATURE_A_ENABLED=
@echo --- scons:build:end ---
@echo.
@echo --- scons:clean:beg ---
@"%PYEXE%" "%SCONS_ROOT%\scripts\scons.py" --site-dir="%SCONS_SITEDIR%" -Qn --clean %_SCONS_MSVC_COMPILER% --scanner=%_SCONS_SCANNER% --FEATURE_A_ENABLED=
@echo --- scons:clean:end ---

@echo.
@echo --- scons:deps:beg ---
@"%PYEXE%" "%SCONS_ROOT%\scripts\scons.py" --site-dir="%SCONS_SITEDIR%" -Qn --scanner-deps %_SCONS_MSVC_COMPILER% --scanner=%_SCONS_SCANNER% --FEATURE_A_ENABLED=0 --expected-map="{'main.c': []}"
@echo --- scons:deps:end ---
@echo.
@echo --- scons:build:beg ---
@"%PYEXE%" "%SCONS_ROOT%\scripts\scons.py" --site-dir="%SCONS_SITEDIR%" -Qn --tree=all %_SCONS_MSVC_COMPILER% --scanner=%_SCONS_SCANNER% --FEATURE_A_ENABLED=0
@echo --- scons:build:end ---
@echo.
@echo --- scons:clean:beg ---
@"%PYEXE%" "%SCONS_ROOT%\scripts\scons.py" --site-dir="%SCONS_SITEDIR%" -Qn --clean %_SCONS_MSVC_COMPILER% --scanner=%_SCONS_SCANNER% --FEATURE_A_ENABLED=0
@echo --- scons:clean:end ---

@echo.
@echo --- scons:deps:beg ---
@"%PYEXE%" "%SCONS_ROOT%\scripts\scons.py" --site-dir="%SCONS_SITEDIR%" -Qn --scanner-deps %_SCONS_MSVC_COMPILER% --scanner=%_SCONS_SCANNER% --FEATURE_A_ENABLED=None --expected-map="{'main.c': ['header1.h']}"
@echo --- scons:deps:end ---
@echo.
@echo --- scons:build:beg ---
@"%PYEXE%" "%SCONS_ROOT%\scripts\scons.py" --site-dir="%SCONS_SITEDIR%" -Qn --tree=all %_SCONS_MSVC_COMPILER% --scanner=%_SCONS_SCANNER% --FEATURE_A_ENABLED=None
@echo --- scons:build:end ---
@echo.
@echo --- scons:clean:beg ---
@"%PYEXE%" "%SCONS_ROOT%\scripts\scons.py" --site-dir="%SCONS_SITEDIR%" -Qn --clean %_SCONS_MSVC_COMPILER% --scanner=%_SCONS_SCANNER% --FEATURE_A_ENABLED=None
@echo --- scons:clean:end ---

@echo.
@echo --- scons:deps:beg ---
@"%PYEXE%" "%SCONS_ROOT%\scripts\scons.py" --site-dir="%SCONS_SITEDIR%" -Qn --scanner-deps %_SCONS_MSVC_COMPILER% --scanner=%_SCONS_SCANNER% --FEATURE_A_ENABLED=1 --expected-map="{'main.c': ['header1.h']}"
@echo --- scons:deps:end ---
@echo.
@echo --- scons:build:beg ---
@"%PYEXE%" "%SCONS_ROOT%\scripts\scons.py" --site-dir="%SCONS_SITEDIR%" -Qn --tree=all %_SCONS_MSVC_COMPILER% --scanner=%_SCONS_SCANNER% --FEATURE_A_ENABLED=1
@echo --- scons:build:end ---
@echo.
@echo --- scons:clean:beg ---
@"%PYEXE%" "%SCONS_ROOT%\scripts\scons.py" --site-dir="%SCONS_SITEDIR%" -Qn --clean %_SCONS_MSVC_COMPILER% --scanner=%_SCONS_SCANNER% --FEATURE_A_ENABLED=1
@echo --- scons:clean:end ---

@echo.

@if exist .sconsign.dblite @del /Q .sconsign.dblite

@popd

@endlocal
@goto :eof

