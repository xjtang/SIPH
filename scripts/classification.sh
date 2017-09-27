#!/bin/bash

# bash script to classify time series segments

# Input Arguments:
#		-t output map type
#		-R recursive
#		--overwrite overwrite
#		ori: origin
#		des: destination
#   img: example image

# default values
type=cls
overwrite=''
recursive=''

# parse input arguments
while [[ $# > 0 ]]; do
	InArg="$1"
	case $InArg in
		-t)
			type=$2
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
      img=$3
			break
	esac
	shift
done

# submit jobs
echo 'Submitting job for craeting' $type 'map.'
qsub -N Classification -V -b y cd /projectnb/landsat/users/xjtang/documents/';' python -m VNRT.classification ${overwrite}${recursive}-t $type $ori $des $img
