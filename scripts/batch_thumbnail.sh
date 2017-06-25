#!/bin/bash

# bash script to preprocess viirs data

# Input Arguments:
#   -p searching pattern
#   -n number of jobs
#   --overwrite overwrite
#   -c band composite
#   -s image stretch
#   -m mask band
#   --combo combine masked and original image
#   ori: origin
#   des: destination

# default values
pattern=VNP*tif
njob=1
overwrite=0
r=3
g=2
b=1
s1=0
s2=5000
mask=0
combo=0

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
    -c)
			r=$2
			g=$3
      b=$4
			shift
      shift
			shift
			;;
    -s)
      s1=$2
      s2=$3
      shift
      shift
      ;;
    -m)
      mask=$2
      shift
      ;;
    --combo)
			combo=1
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
    if [ $combo = 0 ]; then
      qsub -N VNRT_$i ./thumbnail.sh -p $pattern -b $i $njob -c $r $g $b -s $s1 $s2 -m $mask $ori $des
    elif [ $combo = 1 ]; then
      qsub -N VNRT_$i ./thumbnail.sh --combo -p $pattern -b $i $njob -c $r $g $b -s $s1 $s2 -m $mask $ori $des
    fi
  elif [ $overwrite = 1 ]; then
    if [ $combo = 0 ]; then
      qsub -N VNRT_$i ./thumbnail.sh --overwrite -p $pattern -b $i $njob -c $r $g $b -s $s1 $s2 -m $mask $ori $des
    elif [ $combo = 1 ]; then
      qsub -N VNRT_$i ./thumbnail.sh --overwrite --combo -p $pattern -b $i $njob -c $r $g $b -s $s1 $s2 -m $mask $ori $des
    fi
  fi
done
