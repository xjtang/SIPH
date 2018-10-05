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
stable=''

# parse input arguments
while [[ $# > 0 ]]; do
	InArg="$1"
	case $InArg in
		-b)
			bit=$2
			shift
			;;
		-s)
			stable='-s '
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
qsub -j y -N CompareMap -V -b y cd /projectnb/landsat/users/xjtang/documents/';' python -m SIPH.models.chart.compare_maps ${overwrite}${stable}-b $bit $map1 $map2 $des
