#!/bin/bash

# bash script to preprocess VIIRS data

# Input Arguments:
#		-p searching pattern
#		-n number of jobs
#		-R recursive
#		--overwrite overwrite
#		ori: origin
#		des: destination

# default values
pattern=VNP09GA*h5
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
    qsub -j y -N Preprocess_$i -V -b y cd /projectnb/landsat/users/xjtang/documents/';' python -m SIPH.models.vnrt.preprocess ${overwrite}${recursive}-p $pattern -b $i $njob $ori $des
done
