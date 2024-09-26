@setlocal

@set SCONS_BRANCH=../jbrill-mscommon-debug
@set PYTHONPATH=%SCONS_BRANCH%

@set TEST_HOME=%~dp0
@if %TEST_HOME:~-1%==\ set TEST_HOME=%TEST_HOME:~0,-1%

@set "TEST_FOLDER=%TEST_HOME%\Folder With Spaces"
@if not exist "%TEST_FOLDER%" @mkdir "%TEST_FOLDER%

:: ====BEG TESTS====

@rem PASS: path with spaces
@set SCONS_MSCOMMON_DEBUG=%TEST_HOME%\Folder With Spaces\debug1.txt
@call :run-scons

@rem PASS: path with spaces (double quotes around variable assignment)
@set "SCONS_MSCOMMON_DEBUG=%TEST_HOME%\Folder With Spaces\debug2.txt"
@call :run-scons

@rem WARN/PASS: leading and trailing double quotes enclosing filename
@set SCONS_MSCOMMON_DEBUG="%TEST_HOME%\Folder With Spaces\debug3.txt"
@call :run-scons

@rem WARN/FAIL: illegal character (leading ")
@set SCONS_MSCOMMON_DEBUG="%TEST_HOME%\Folder With Spaces\debug4.txt
@call :run-scons

@rem WARN/FAIL: illegal character (trailing ")
@set SCONS_MSCOMMON_DEBUG=%TEST_HOME%\Folder With Spaces\debug5.txt"
@call :run-scons

@rem WARN/FAIL: illegal character (embedded ")
@set SCONS_MSCOMMON_DEBUG=%TEST_HOME%\Folder With Spaces\dqbeg"dqend.txt
@call :run-scons

@rem WARN/FAIL: illegal character (embedded ?)
@set SCONS_MSCOMMON_DEBUG=%TEST_HOME%\Folder With Spaces\qmarkbeg?qmarkend.txt
@call :run-scons

@rem WARN/PASS: false positive (embedded : in file name)
@rem creates file "colonbeg" and hidden file "colonbeg:colonend.txt$DATA"
@set SCONS_MSCOMMON_DEBUG=%TEST_HOME%\Folder With Spaces\colonbeg:colonend.txt
@call :run-scons

@rem WARN/FAIL: reserved name (AUX)
@set SCONS_MSCOMMON_DEBUG=%TEST_HOME%\Folder With Spaces\aux.txt
@call :run-scons

@rem WARN/FAIL: file name is a directory
@set SCONS_MSCOMMON_DEBUG=%TEST_HOME%\Folder With Spaces\
@call :run-scons

@rem PASS: (not reserved name)
@set SCONS_MSCOMMON_DEBUG=%TEST_HOME%\Folder With Spaces\prn1.txt
@call :run-scons

@rem PASS: (reserved name preceded by spaces)
@set SCONS_MSCOMMON_DEBUG=%TEST_HOME%\Folder With Spaces\ con.txt
@call :run-scons

:: ====END TESTS====

@endlocal
@goto :eof

:run-scons
    @if exist .sconsign.dblite @del .sconsign.dblite
    @echo ==========BEGIN============
    @echo SCONS_MSCOMMON_DEBUG=%SCONS_MSCOMMON_DEBUG%
    :: @python -m SCons
    @python %SCONS_BRANCH%/scripts/scons.py
    @echo ===========================
    @echo.
    @if exist .sconsign.dblite @del .sconsign.dblite
    @goto :eof