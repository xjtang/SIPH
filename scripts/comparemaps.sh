#!/bin/bash

# bash script to compare two maps

# Input Arguments:
#		-b bitshift
#		--overwrite overwrite
#		map1: map1 origin
#   map2: map2 origin
#		des: destination

# default values
bit=3
overwrite=''
recursive=''

# parse input arguments
while [[ $# > 0 ]]; do
	InArg="$1"
	case $InArg in
		-b)
			bitshift=$2
			shift
			;;
		--overwrite)
			overwrite='--overwrite '
			;;
		*)
      map1=$1
      map2=$2
			des=$3
			break
	esac
	shift
done

# submit jobs
qsub -j y -N CompareMap -V -b y cd /projectnb/landsat/users/xjtang/documents/';' python -m SIPH.models.chart.compare_maps ${overwrite}-b $bit $map1 $map2 $des
