#!/bin/bash

# bash script to refine classification results

# Input Arguments:
#		--overwrite overwrite
#		mekong: mekong map
#   krishna: krishna map
#		des: destination

# default values
overwrite=''

# parse input arguments
while [[ $# > 0 ]]; do
	InArg="$1"
	case $InArg in
		--overwrite)
			overwrite='--overwrite '
			;;
		*)
      mekong=$1
      krishna=$2
			des=$3
			break
	esac
	shift
done

# submit job
echo 'Submitting job to refine classification results'
qsub -l mem_total=94G -j y -N Refine -V -b y cd /projectnb/landsat/users/xjtang/documents/';' python -m SIPH.models.chart.refine4 ${overwrite} $mekong $krishna $des
