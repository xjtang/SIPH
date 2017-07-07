#!/bin/bash

# bash script to convert csv to shapefile

# Input Arguments:
#   -p searching pattern
#   -n number of jobs
#   --overwrite overwrite
#   -e EPSG
#   ori: origin
#   des: destination

# default values
pattern=M*csv
njob=1
overwrite=0
epsg=3857

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
    -e)
			epsg=$2
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

# submit jobs
echo 'Total jobs to submit is' $njob
for i in $(seq 1 $njob); do
  echo 'Submitting job no.' $i 'out of' $njob
  if [ $overwrite = 0 ]; then
    qsub -N CSV2SHP_$i ./csv2shape.sh -p $pattern -b $i $njob -e $epsg $ori $des
  elif [ $overwrite = 1 ]; then
    qsub -N CSV2SHP_$i ./csv2shape.sh --overwrite -p $pattern -b $i $njob -e $epsg $ori $des
  fi
done
