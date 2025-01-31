#!/bin/bash

# https://stackoverflow.com/questions/59895/how-do-i-get-the-directory-where-a-bash-script-is-located-from-within-the-script
SCRIPT_ROOT=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

if [[ -z "${SCONS_ROOT}" ]]; then
    SCONS_ROOT="${SCRIPT_ROOT}/../../scons-master"
fi

if [[ -z "${SCONS_SITEDIR}" ]]; then
    SCONS_SITEDIR="${SCRIPT_ROOT}/../site-scons"
fi

TEST_ROOT="${SCRIPT_ROOT}/IncSysPathTest"

if [[ -z "${1}" ]]; then
    _SCONS_SCANNER=CPreProcessorScanner
else
    _SCONS_SCANNER=${1}
fi

pushd "${TEST_ROOT}" > /dev/null

rm -f ./.sconsign.dblite

echo
echo --- scons:deps:beg ---
python "${SCONS_ROOT}/scripts/scons.py" --site-dir="${SCONS_SITEDIR}" -Qn --scanner-deps --scanner=${_SCONS_SCANNER} --expected-map="{'main.c': ['include/include.h']}"
echo --- scons:deps:end ---
echo
echo --- scons:build:beg ---
python "${SCONS_ROOT}/scripts/scons.py" --site-dir="${SCONS_SITEDIR}" -Qn --tree=all --scanner=${_SCONS_SCANNER}
echo --- scons:build:end ---
echo
echo --- scons:clean:beg ---
python "${SCONS_ROOT}/scripts/scons.py" --site-dir="${SCONS_SITEDIR}" -Qn --clean --scanner=${_SCONS_SCANNER}
echo --- scons:clean:end ---

echo

rm -f ./.sconsign.dblite

popd > /dev/null