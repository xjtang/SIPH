#!/bin/bash

# bash script to generating image highlighting pixels over the SD threshold

# Input Arguments:
#		-n number of jobs
#		-p searching pattern
#		-R recursive
#		--overwrite overwrite
#		ori: origin
#		des: destination
#   img: an example image to get the spatial reference

# default values
njob=1
pattern=ts*mat
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
      img=$3
			break
	esac
	shift
done

# submit jobs
echo 'Total jobs to submit is' $njob
for i in $(seq 1 $njob); do
  echo 'Submitting job no.' $i 'out of' $njob
  qsub -N sdt_$i -V -b y cd /usr3/graduate/xjtang/Documents/';' python -m VNRT.fusion.area_over_threshold ${overwrite}${recursive}-p $pattern -b $i $njob $ori $des $img
done
