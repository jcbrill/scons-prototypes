#!/bin/bash

# https://stackoverflow.com/questions/59895/how-do-i-get-the-directory-where-a-bash-script-is-located-from-within-the-script
SCRIPT_ROOT=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# export SCONS_ROOT to scons root directory

echo
echo ++++++ GCCProcessorScanner:beg ++++++
"${SCRIPT_ROOT}/_run-example-01-tests.sh" CPreProcessorScanner
echo ++++++ GCCProcessorScanner:end ++++++

echo
