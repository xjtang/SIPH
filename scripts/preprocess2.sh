#!/bin/bash

# bash script to preprocess viirs data

# Input Arguments:
#		-p searching pattern
#		-n number of jobs
#   -Q location to look for 250m data
#		-R recursive
#		--overwrite overwrite
#		ori: origin
#		des: destination

# default values
pattern=MOD09GA*hdf
njob=1
overwrite=''
recursive=''
mgq='NA'

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
    -Q)
      mgq=$2
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
echo 'Total jobs to submit is' $njob
for i in $(seq 1 $njob); do
    echo 'Submitting job no.' $i 'out of' $njob
    qsub -j y -N Preprocess_$i -V -b y cd /projectnb/landsat/users/xjtang/documents/';' python -m SIPH.models.vnrt.preprocess2 ${overwrite}${recursive}-p $pattern -Q mgq -b $i $njob $ori $des
done
