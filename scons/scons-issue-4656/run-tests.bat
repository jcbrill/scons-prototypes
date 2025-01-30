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

call "%SCRIPT_ROOT%\tests\comment-tests.bat" >"%SCRIPT_ROOT%\output\win-output%SCONS_ROOT_LABEL%-comment-tests.txt" 2>&1
call "%SCRIPT_ROOT%\tests\incsyspath-tests.bat" >"%SCRIPT_ROOT%\output\win-output%SCONS_ROOT_LABEL%-incsyspath-tests.txt" 2>&1
call "%SCRIPT_ROOT%\tests\issue-tests.bat" >"%SCRIPT_ROOT%\output\win-output%SCONS_ROOT_LABEL%-issue-tests.txt" 2>&1
call "%SCRIPT_ROOT%\tests\known-tests.bat" >"%SCRIPT_ROOT%\output\win-output%SCONS_ROOT_LABEL%-known-tests.txt" 2>&1
call "%SCRIPT_ROOT%\tests\macro-tests.bat" >"%SCRIPT_ROOT%\output\win-output%SCONS_ROOT_LABEL%-macro-tests.txt" 2>&1
call "%SCRIPT_ROOT%\tests\multiple-tests.bat" >"%SCRIPT_ROOT%\output\win-output%SCONS_ROOT_LABEL%-multiple-tests.txt" 2>&1
call "%SCRIPT_ROOT%\tests\recurse-tests.bat" >"%SCRIPT_ROOT%\output\win-output%SCONS_ROOT_LABEL%-recurse-tests.txt" 2>&1
call "%SCRIPT_ROOT%\tests\scanner-tests.bat" >"%SCRIPT_ROOT%\output\win-output%SCONS_ROOT_LABEL%-scanner-tests.txt" 2>&1

@endlocal