#!/bin/bash

# bash script to merge image with masks

# Input Arguments:
#		-p searching pattern
#		-n number of jobs
#		-m mask band
#   -v mask value
#		-R recursive
#		--overwrite overwrite
#		ori: origin
#		des: destination

# default values
pattern=S*tif
njob=1
mask='-m 9 10 11 '
value='-v 2 4 '
overwrite=''
recursive=''
reclass=''

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
      mask='-m '$2' '$3' '$4' '
      shift
      shift
      shift
      ;;
    -v)
      value='-v '$2' '$3' '
      shift
      shift
      ;;
		-r)
			reclass='-r '
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
    qsub -j y -N HLS_$i -V -b y cd /projectnb/landsat/users/xjtang/documents/';' python -m SIPH.models.hls.strata ${mask}${value}${overwrite}${recursive}${reclass}-p $pattern -b $i $njob $ori $des
done
