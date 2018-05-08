#!/bin/bash

# bash script to generate maps from YATSM results

# Input Arguments:
#   -t type of map
#   -o options
#		-R recursive
#		--overwrite overwrite
#		ori: origin
#		des: destination
#   img: image for spatial reference

# default values
type=change
option=0
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
    -o)
			option=$2
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
echo 'Submitting single job.'
qsub -j y -N CHART -V -b y cd /projectnb/landsat/users/xjtang/documents/';' python -m SIPH.models.chart.yatsm_to_maps ${overwrite}${recursive}-o $option -t $type $ori $des $img
