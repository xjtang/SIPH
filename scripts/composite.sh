#!/bin/bash

# bash script to create MODIS composite

# Input Arguments:
#		-p searching pattern
#		-n number of jobs
#		-R recursive
#		--overwrite overwrite
#		terra: terra origin
#   aqua: aqua origin
#		des: destination

# default values
pattern=MOD*tif
njob=1
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
		-n)
			njob=$2
			shift
			;;
		-R)
			recursive='-R '
			;;
		--overwrite)
			overwrite='--overwrite '
			;;
		*)
      terra=$1
      aqua=$2
			des=$3
			break
	esac
	shift
done

# submit jobs
echo 'Total jobs to submit is' $njob
for i in $(seq 1 $njob); do
    echo 'Submitting job no.' $i 'out of' $njob
    qsub -j y -N Composite_$i -V -b y cd /projectnb/landsat/users/xjtang/documents/';' python -m SIPH.models.vnrt.composite ${overwrite}${recursive}-p $pattern -b $i $njob $terra $aqua $des
done
