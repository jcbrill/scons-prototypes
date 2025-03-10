@setlocal

@set "SCRIPT_ROOT=%~dp0"
@if "%SCRIPT_ROOT:~-1%" == "\" set "SCRIPT_ROOT=%SCRIPT_ROOT:~0,-1%"

:: set PYEXE to fully qualified python executable
:: @set PYEXE=...

@set "SCONS_ROOT=%SCRIPT_ROOT%\..\scons-master"
@set SCONS_ROOT_LABEL=

@set "SCONS_SITEDIR=%SCRIPT_ROOT%\site-scons"

@set "SCONS_CACHE_MSVC_CONFIG=%SCRIPT_ROOT%\_scons_msvc_cache.json"

@if not exist "%SCRIPT_ROOT%\output" @mkdir "%SCRIPT_ROOT%\output"

call "%SCRIPT_ROOT%\examples\run-example-01.bat" >"%SCRIPT_ROOT%\output\win-output%SCONS_ROOT_LABEL%-example-01.txt" 2>&1

@endlocal