#!/bin/bash

# bash script to merge image with masks

# Input Arguments:
#		-p searching pattern
#		-R recursive
#		--overwrite overwrite
#   n: number of samples
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
      n=$1
      ori=$2
			des=$3
			break
	esac
	shift
done

# submit jobs
echo 'Submitting job to select samples.'
qsub -j y -N SAMPLE -V -b y cd /projectnb/landsat/users/xjtang/documents/';' python -m SIPH.models.accuracy.random_samples -s 2 3 4 5 ${overwrite}${recursive}-p $pattern $n $ori $des
