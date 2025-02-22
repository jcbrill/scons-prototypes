@setlocal

@set "SCRIPT_ROOT=%~dp0"
@if "%SCRIPT_ROOT:~-1%" == "\" set "SCRIPT_ROOT=%SCRIPT_ROOT:~0,-1%"

:: set PYEXE to fully qualified python executable
:: set SCONS_ROOT to scons root directory

@echo.
@echo ++++++ GCCProcessorScanner:beg ++++++
@call "%SCRIPT_ROOT%\_run-example-01-tests.bat" CPreProcessorScanner
@echo ++++++ GCCProcessorScanner:end ++++++

@echo.
@echo ++++++ MSVCProcessorScanner:beg ++++++
@call "%SCRIPT_ROOT%\_run-example-01-tests.bat" CPreProcessorScanner --msvc-compiler
@echo ++++++ MSVCProcessorScanner:end ++++++

@echo.

@endlocal

