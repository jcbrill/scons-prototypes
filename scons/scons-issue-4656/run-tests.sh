#!/bin/bash

# https://stackoverflow.com/questions/59895/how-do-i-get-the-directory-where-a-bash-script-is-located-from-within-the-script
SCRIPT_ROOT=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# export SCONS_ROOT to scons root directory

export SCONS_ROOT="${SCRIPT_ROOT}/../scons-master"
SCONS_ROOT_LABEL=

export SCONS_SITEDIR="${SCRIPT_ROOT}/site-scons"

mkdir -p "${SCRIPT_ROOT}/output"
set -x

"${SCRIPT_ROOT}/tests/comment-tests.sh" >"${SCRIPT_ROOT}/output/wsl-output${SCONS_ROOT_LABEL}-comment-tests.txt" 2>&1
"${SCRIPT_ROOT}/tests/incsyspath-tests.sh" >"${SCRIPT_ROOT}/output/wsl-output${SCONS_ROOT_LABEL}-incsyspath-tests.txt" 2>&1
"${SCRIPT_ROOT}/tests/issue-tests.sh" >"${SCRIPT_ROOT}/output/wsl-output${SCONS_ROOT_LABEL}-issue-tests.txt" 2>&1
"${SCRIPT_ROOT}/tests/macro-tests.sh" >"${SCRIPT_ROOT}/output/wsl-output${SCONS_ROOT_LABEL}-macro-tests.txt" 2>&1
"${SCRIPT_ROOT}/tests/multiple-tests.sh" >"${SCRIPT_ROOT}/output/wsl-output${SCONS_ROOT_LABEL}-multiple-tests.txt" 2>&1
"${SCRIPT_ROOT}/tests/recurse-tests.sh" >"${SCRIPT_ROOT}/output/wsl-output${SCONS_ROOT_LABEL}-recurse-tests.txt" 2>&1
"${SCRIPT_ROOT}/tests/scanner-tests.sh" >"${SCRIPT_ROOT}/output/wsl-output${SCONS_ROOT_LABEL}-scanner-tests.txt" 2>&1
