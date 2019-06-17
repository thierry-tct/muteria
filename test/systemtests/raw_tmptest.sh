#! /bin/bash

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
		python3 --version > /dev/null || error_exit "'python' represent earlier python version( < 3.0) and python3 not existing"
		python_exe=python3
		pip_exe=pip3
	fi
}

##

ensure_python_version

topdir=$(dirname $(readlink -f $0))
py_prog_folder=example_python
c_prog_folder=example_c

muteria_topdir=$topdir/../..

for prog_folder in $py_prog_folder $c_prog_folder
do
	echo "-- RUNNING $prog_folder"
	echo ""
	
	clean_data=$topdir/$prog_folder
	tmp_workspace=$topdir/tmp.work.delete
	workdata=$tmp_workspace/$prog_folder
	workdata_repo=$workdata/repo
	workdata_ctrl=$workdata/ctrl

	entry_point=$topdir/run.py

	rm -rf $tmp_workspace
	mkdir $tmp_workspace || error_exit "failed creating tmp_workspace"
	cp -rf $clean_data $tmp_workspace || error_exit "failed to copy clean into tmp_workspace"

	$python_exe $entry_point $muteria_topdir $workdata_ctrl || error_exit "test failed for $prog_folder"

	echo "Press any key to continue (done with $prog_folder)"
	read x #-t 3 -n 1

	rm -rf $tmp_workspace
done