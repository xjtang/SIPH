#!/bin/bash

# bash script to preprocess viirs data

# Input Arguments:
#   -p searching pattern
#   -b batch jobs, [thisjob, totaljob]
#   --overwrite overwrite
#   ori: origin
#   des: destination

# Settings:
#$ -S /bin/bash
#$ -l h_rt=24:00:00
#$ -V
#$ -N Preprocess

# default values
pattern=VNP09GA*h5
thisjob=1
totaljob=1
overwrite=0

# parse input arguments
while [[ $# > 0 ]]; do
	InArg="$1"
	case $InArg in
		-p)
			pattern=$2
			shift
			;;
		-b)
			thisjob=$2
			totaljob=$3
			shift
			shift
			;;
		--overwrite)
			overwrite=1
			;;
		*)
      ori=$1
			des=$2
			break
	esac
	shift
done

# run python script
cd /usr3/graduate/xjtang/Documents/
if [ $overwrite = 0 ]; then
	python -m VNRT.preprocess -p $pattern -b $thisjob $totaljob $ori $des
elif [ $overwrite = 1 ]; then
  python -m VNRT.preprocess --overwrite -p $pattern -b $thisjob $totaljob $ori $des
fi
