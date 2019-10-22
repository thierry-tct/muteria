#! /bin/bash
# RUN: $0 <arguments>
set -u

error_exit()
{
	echo "# ERROR: $1"
	exit 1
}

ensure_python_version()
{
	python_exe=python
	pip_exe=pip
	major=$($python_exe --version 2>&1 | awk '{print $2}' | cut -d'.' -f1)
	if [ "$major" != "" -a $major -lt 3 ]
	then
		# check that python3 is on the path
		python3 --version > /dev/null || error_exit "'python' represent earlier python version(< 3.0) and python3 not existing"
		python_exe=python3
		pip_exe=pip3
	fi
}

##
ensure_python_version

topdir=$(dirname $(readlink -f $0))

muteria_topdir=$(readlink -f $topdir/../..)

PYTHONPATH=$muteria_topdir $python_exe $topdir/cli.py "${@:1}"
