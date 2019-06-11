#! /bin/bash

set -u

error_exit()
{
	echo "# ERROR: $1"
	exit 1
}

topdir=$(dirname $(readlink -f $0))
prog_folder=example_python

muteria_topdir=$topdir/../..

clean_data=$topdir/$prog_folder
tmp_workspace=$topdir/tmp.work.delete
workdata=$tmp_workspace/$prog_folder
workdata_repo=$workdata/repo
workdata_ctrl=$workdata/ctrl

entry_point=$workdata_ctrl/run.py

rm -rf $tmp_workspace
mkdir $tmp_workspace || error_exit "failed creating tmp_workspace"
cp -rf $clean_data $tmp_workspace || error_exit "failed to copy clean into tmp_workspace"

python $entry_point $muteria_topdir || error_exit "test failed"

rm -rf $tmp_workspace
