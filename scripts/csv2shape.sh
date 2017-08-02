#!/bin/bash

# bash script to convert csv to shapefile

# Input Arguments:
#		-p searching pattern
#		-n number of jobs
#		-R recursive
#		--overwrite overwrite
#		-e EPSG
#		ori: origin
#		des: destination

# default values
pattern=M*csv
njob=1
overwrite=''
recursive=''
epsg=3857

## parse input arguments
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
    -e)
			epsg=$2
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
    qsub -N CSV2SHP_$i -V -b y cd /usr3/graduate/xjtang/Documents/';' python -m VNRT.tools.swath_footprint ${overwrite}${recursive}-p $pattern -b $i $njob -e $epsg $ori $des
done
