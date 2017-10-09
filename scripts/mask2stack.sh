#!/bin/bash

# bash script to convert mask images to stacked images

# Input Arguments:
#		-p searching pattern
#		-n number of jobs
#		-m mask source
#		-R recursive
#		--overwrite overwrite
#		ori: origin
#		des: destination

# default values
pattern=HLS*fmask*hdf
njob=1
mask=fmask
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
    -m)
      mask=$2
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
    qsub -N HLS_$i -V -b y cd /projectnb/landsat/users/xjtang/documents/';' python -m VNRT.hls.mask_to_stack ${overwrite}${recursive}-p $pattern -b $i $njob -m $mask $ori $des
done
