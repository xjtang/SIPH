#!/bin/bash

# bash script to generate map from blended results

# Input Arguments:
#		-R recursive
#		--overwrite overwrite
#		ori: origin
#		des: destination
#   img: example image

# default values
overwrite=''
recursive=''
lc=NA

# parse input arguments
while [[ $# > 0 ]]; do
	InArg="$1"
	case $InArg in
		-l)
			lc=$2
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
echo 'Submitting job to generate map from blended results.'
qsub -j y -N CHART -V -b y cd /projectnb/landsat/users/xjtang/documents/';' python -m SIPH.models.chart.blend_to_maps -l $lc ${overwrite}${recursive}$ori $des $img
