#!/bin/bash

# bash script to export stack image as refular image

# Input Arguments:
#		-n number of jobs
#		-p searching pattern
#		-c band composite
#		-s image stretch
#		-f output image format (e.g. rgb)
#		-m mask band
#		-r result image
#		-w crop window
#		-R recursive
#		--overwrite overwrite
#		ori: origin
#		des: destination

# default values
njob=1
pattern=VNP*tif
overwrite=''
recursive=''
w=''
r=3
g=2
b=1
s1=0
s2=5000
format=rgb
mask=0
result=NA

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
			w='-w '$2' '$3' '$4' '$5' '
			shift
			shift
			shift
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
  qsub -N stack2image_$i -V -b y cd /usr3/graduate/xjtang/Documents/';' python -m VNRT.tools.export_image ${overwrite}${recursive}${w}-p $pattern -b $i $njob -c $r $g $b -s $s1 $s2 -m $mask -f $format -r $result $ori $des
done
