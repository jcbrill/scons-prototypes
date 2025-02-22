#!/bin/bash

# https://stackoverflow.com/questions/59895/how-do-i-get-the-directory-where-a-bash-script-is-located-from-within-the-script
SCRIPT_ROOT=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# export SCONS_ROOT to scons root directory

export SCONS_ROOT="${SCRIPT_ROOT}/../scons-master"
SCONS_ROOT_LABEL=

export SCONS_SITEDIR="${SCRIPT_ROOT}/site-scons"

mkdir -p "${SCRIPT_ROOT}/output"
set -x

"${SCRIPT_ROOT}/examples/run-example-01.sh" >"${SCRIPT_ROOT}/output/wsl-output${SCONS_ROOT_LABEL}-example-01.txt" 2>&1
