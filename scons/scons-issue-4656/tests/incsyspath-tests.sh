#!/bin/bash

# https://stackoverflow.com/questions/59895/how-do-i-get-the-directory-where-a-bash-script-is-located-from-within-the-script
SCRIPT_ROOT=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# export SCONS_ROOT to scons root directory

echo
echo ++++++ GCCProcessorScanner:beg ++++++
"${SCRIPT_ROOT}/_run-incsyspath-tests.sh" CPreProcessorScanner
echo ++++++ GCCProcessorScanner:end ++++++

echo
echo ++++++ CConditionalModScanner:beg ++++++
"${SCRIPT_ROOT}/_run-incsyspath-tests.sh" CConditionalModScanner
echo ++++++ CConditionalModScanner:end ++++++

echo
echo ++++++ CConditionalScanner:beg ++++++
"${SCRIPT_ROOT}/_run-incsyspath-tests.sh" CConditionalScanner
echo ++++++ CConditionalScanner:end ++++++

echo
echo ++++++ CScanner:beg ++++++
"${SCRIPT_ROOT}/_run-incsyspath-tests.sh" CScanner
echo ++++++ CScanner:end ++++++

echo
