#!/bin/bash

# Submit job to preprocess viirs data

# Input Arguments:
#   -p searching pattern
#   -b batch jobs, [thisjob, totaljob]
#   --overwrite overwrite
#   ori origin
#   des destination

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
			shift
			;;
		*)
      ori=$1
			des=$2
			break
	esac

	shift

done

# load environment
module purge
module load python/2.7.13
module load sqlite3/3.17.0
module load proj4/4.8.0
module load libgta/1.0.5
module load hdf/4.2.11_no_netcdf
module load hdf5/1.8.16
module load netcdf/4.4.0
module load jasper/1.900.1
module load ecw/3.3.20060906
module load mrsid_dsdk/9.1.0.4045
module load xerces-c/3.1.1
module load libkml/1.3.0
module load libdap/3.12.0
module load geos/3.6.1
module load freexl/1.0.2
module load libspatialite/4.3.0a
module load epsilon/0.9.2
module load webp/0.4.2
module load postgresql/9.4.4
module load gdal/2.1.3

# run python script
cd /usr3/graduate/xjtang/Documents/
if [ $overwrite = 0 ]; then
	python -m VNRT.preprocess -p $pattern -b $thisjob $totaljob $ori $des
elif [ $overwrite = 1 ]; then
  python -m VNRT.preprocess --overwrite -p $pattern -b $thisjob $totaljob $ori $des
fi
