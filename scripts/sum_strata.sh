#!/bin/bash

# bash script to summarize strata

# Input Arguments:
#		-p searching pattern
#		-R recursive
#		--overwrite overwrite
#		ori: origin
#		des: destination

# default values
pattern=*strata*tif
overwrite=''
recursive=''

# parse input arguments
while [[ $# > 0 ]]; do
	InArg="$1"
	case $InArg in
		-p)
			pattern=$2
			shift
			;;
		-R)
			recursive='-R '
			;;
		--overwrite)
			overwrite='--overwrite '
			;;
		*)
      ori=$1
			des=$2
			break
	esac
	shift
done

# submit jobs
echo 'Submitting job...'
qsub -j y -N STRATA -V -b y cd /projectnb/landsat/users/xjtang/documents/';' python -m SIPH.models.hls.sum_strata ${overwrite}${recursive}-p $pattern $ori $des
