#! /bin/bash
# RUN: $0 [<example to run>?]
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

###


# List of tests to run
TestList=(example_python example_c)


only_example=''
if [ $# -eq 1 -o $# -eq 2 ]
then
	only_example="$1"
	echo "${TestList[@]}" | tr ' ' '\n' | grep "^$only_example$" > /dev/null || error_exit "invalid test: $only_example"
	just_continue=0
	if [ $# -eq 2 ]; then
		if [ "$2" = "continue" ]; then
			just_continue=1
		else
			error_exit "invalid secon parameter. expect 'continue'"
		fi
	fi
fi

ensure_python_version

topdir=$(dirname $(readlink -f $0))

muteria_topdir=$topdir/../..

for prog_folder in "${TestList[@]}"
do
	if [ "$only_example" != '' ]
	then
		[ "$prog_folder" != "$only_example" ] && continue
	fi

	echo "-- RUNNING $prog_folder"
	echo ""
	
	clean_data=$topdir/$prog_folder
	tmp_workspace=$topdir/tmp.work.delete
	workdata=$tmp_workspace/$prog_folder
	workdata_repo=$workdata/repo
	workdata_ctrl=$workdata/ctrl

	entry_point=$topdir/run.py

	if [ $just_continue -eq 1 ] && `test -d $tmp_workspace/$prog_folder`
	then
		echo
		echo "# CONTINUING..."
		echo
	else
		rm -rf $tmp_workspace
		mkdir $tmp_workspace || error_exit "failed creating tmp_workspace"
		cp -rf $clean_data $tmp_workspace || error_exit "failed to copy clean into tmp_workspace"

		# Temporary
		if [ "${WITH_SHADOW:-}" = "on" -a -f $tmp_workspace/$prog_folder/ctrl/conf_shadow.py ]
		then
			mv $tmp_workspace/$prog_folder/ctrl/conf_shadow.py $tmp_workspace/$prog_folder/ctrl/conf.py | error_exit "failed to set conf to shadow conf"
			echo "-- Using Shadow !!!"
		elif [ "${WITH_SEMU:-}" = "on" -a -f $tmp_workspace/$prog_folder/ctrl/conf_semu.py ]
		then
			mv $tmp_workspace/$prog_folder/ctrl/conf_semu.py $tmp_workspace/$prog_folder/ctrl/conf.py | error_exit "failed to set conf to semu conf"
			echo "-- Using Semu !!!"
		fi
	fi

	yes | $python_exe $entry_point $muteria_topdir $workdata_ctrl || error_exit "test failed for $prog_folder"

	echo "Press any key to continue (done with $prog_folder)"
	read x #-t 3 -n 1

	rm -rf $tmp_workspace
done
