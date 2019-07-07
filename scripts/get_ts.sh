#!/bin/bash

# bash script to get time series

# Input Arguments:
#		--overwrite overwrite
#   x: x
#   y: y
#		ori: origin
#		des: destination

# default values
x=1
y=1
overwrite=''

# parse input arguments
while [[ $# > 0 ]]; do
	InArg="$1"
	case $InArg in
		--overwrite)
			overwrite='--overwrite '
			;;
		*)
      x=$1
      y=$2
      ori=$3
			des=$4
			break
	esac
	shift
done

# submit jobs
qsub -j y -N GetTS -V -b y cd /projectnb/landsat/users/xjtang/documents/';' python -m SIPH.models.yatsm.get_ts ${overwrite} $x $y $ori $des
