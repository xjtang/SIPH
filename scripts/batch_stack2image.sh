#!/bin/bash

# bash script to export stack image as refular image

# Input Arguments:
#   -n number of jobs
#   -p searching pattern
#   -b batch jobs, [thisjob, totaljob]
#   -c band composite
#   -s image stretch
#		-f output image format (e.g. rgb)
#   -m mask band
#		-r result image
#		-w crop window
#   --overwrite overwrite
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
format=rgb
mask=0
result=NA
w=0

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
		-r)
			result=$2
			shift
			;;
		-f)
			format=$2
			shift
			;;
		-w)
			w=1
			w1=$2
			w2=$3
			w3=$4
			w4=$5
			shift
			shift
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

# submit jobs
echo 'Total jobs to submit is' $njob
for i in $(seq 1 $njob); do
  echo 'Submitting job no.' $i 'out of' $njob
  if [ $overwrite = 0 ]; then
    if [ $w = 0 ]; then
      qsub -N VNRT_$i ./stack2image.sh -p $pattern -b $i $njob -c $r $g $b -s $s1 $s2 -m $mask -r $result -f $format $ori $des
    elif [ $w = 1 ]; then
      qsub -N VNRT_$i ./stack2image.sh -p $pattern -b $i $njob -c $r $g $b -s $s1 $s2 -m $mask -r $result -f $format -w $w1 $w2 $w3 $w4 $ori $des
    fi
  elif [ $overwrite = 1 ]; then
    if [ $w = 0 ]; then
			qsub -N VNRT_$i ./stack2image.sh --overwrite -p $pattern -b $i $njob -c $r $g $b -s $s1 $s2 -m $mask -r $result -f $format $ori $des
    elif [ $w = 1 ]; then
			qsub -N VNRT_$i ./stack2image.sh --overwrite -p $pattern -b $i $njob -c $r $g $b -s $s1 $s2 -m $mask -r $result -f $format -w $w1 $w2 $w3 $w4 $ori $des
    fi
  fi
done
