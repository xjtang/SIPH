#!/bin/bash

# bash script to csv to shapefile

# Input Arguments:
#   -p searching pattern
#   -b batch jobs, [thisjob, totaljob]
#   --overwrite overwrite
#   -e EPSG
#   ori: origin
#   des: destination

# Settings:
#$ -S /bin/bash
#$ -l h_rt=24:00:00
#$ -V
#$ -N csv2shape

# default values
pattern=M*csv
njob=1
overwrite=0
epsg=3857
thisjob=1
totaljob=1

## parse input arguments
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

# run python script
module purge
module load python/2.7.13
cd /usr3/graduate/xjtang/Documents/
if [ $overwrite = 0 ]; then
  python -m VNRT.tools.swath_footprint -p $pattern -b $thisjob $totaljob -e $epsg $ori $des
elif [ $overwrite = 1 ]; then
  python -m VNRT.tools.swath_footprint --overwrite -p $pattern -b $thisjob $totaljob -e $epsg $ori $des
fi
