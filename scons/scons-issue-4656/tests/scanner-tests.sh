#!/bin/bash

# set SCONS_ROOT to scons root directory

# https://stackoverflow.com/questions/59895/how-do-i-get-the-directory-where-a-bash-script-is-located-from-within-the-script
SCRIPT_ROOT=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

if [[ -z "${SCONS_ROOT}" ]]; then
    SCONS_ROOT="${SCRIPT_ROOT}/../../scons-master"
fi

if [[ -z "${SCONS_SITEDIR}" ]]; then
    SCONS_SITEDIR="${SCRIPT_ROOT}/../site-scons"
fi

if [ $# -ge 1 ]; then 
    TEST_ROOT="$1"
else
    TEST_ROOT="${SCRIPT_ROOT}/ScannerTest"
fi

pushd "${TEST_ROOT}" > /dev/null

rm -f ./.sconsign.dblite

echo --- scons:beg ---
python "${SCONS_ROOT}/scripts/scons.py" -Qn --site-dir="${SCONS_SITEDIR}"
echo --- scons:end ---

rm -f ./.sconsign.dblite

popd > /dev/null