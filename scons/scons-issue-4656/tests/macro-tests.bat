@setlocal

@set "SCRIPT_ROOT=%~dp0"
@if "%SCRIPT_ROOT:~-1%" == "\" set "SCRIPT_ROOT=%SCRIPT_ROOT:~0,-1%"

:: set PYEXE to fully qualified python executable
:: set SCONS_ROOT to scons root directory

@echo.
@echo ++++++ GCCProcessorScanner:beg ++++++
@call "%SCRIPT_ROOT%\_run-macro-tests.bat" CPreProcessorScanner
@echo ++++++ GCCProcessorScanner:end ++++++

@echo.
@echo ++++++ MSVCProcessorScanner:beg ++++++
@call "%SCRIPT_ROOT%\_run-macro-tests.bat" CPreProcessorScanner --msvc-compiler
@echo ++++++ MSVCProcessorScanner:end ++++++

@echo.
@echo ++++++ CConditionalModScanner:beg ++++++
@call "%SCRIPT_ROOT%\_run-macro-tests.bat" CConditionalModScanner
@echo ++++++ CConditionalModScanner:end ++++++

@echo.
@echo ++++++ CConditionalScanner:beg ++++++
@call "%SCRIPT_ROOT%\_run-macro-tests.bat" CConditionalScanner
@echo ++++++ CConditionalScanner:end ++++++

@echo.
@echo ++++++ CScanner:beg ++++++
@call "%SCRIPT_ROOT%\_run-macro-tests.bat" CScanner
@echo ++++++ CScanner:end ++++++

@echo.

@endlocal

