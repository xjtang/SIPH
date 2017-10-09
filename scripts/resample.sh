#!/bin/bash

# bash script to convert mask images to stacked images

# Input Arguments:
#		-p searching pattern
#		-m resample method
#   -s output resolution
#		ori: origin
#		des: destination

# default values
pattern=HLS*hdf
method=mode
res=30

# parse input arguments
while [[ $# > 0 ]]; do
	InArg="$1"
	case $InArg in
		-p)
			pattern=$2
			shift
			;;
    -m)
      method=$2
      shift
      ;;
    -s)
      res=$2
      shift
      ;;
		*)
      ori=$1
			des=$2
			break
	esac
	shift
done

# submit jobs
qsub -N RSPL_$i -V -b y find $des -name $pattern -exec sh -c 'gdalwarp -tr $res $res -r $method {} $des/$(basename {})' \;
