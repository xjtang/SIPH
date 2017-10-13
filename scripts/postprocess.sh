#!/bin/bash

# bash script to postprocess vnrt results

# Input Arguments:
#		-w window size, how much to extent out from center pixel
#		-t clean up threhold
#		-d try to clean up the date images in the same folder as well
#		--overwrite overwrite
#		ori: origin
#		des: destination

# default values
w=1
t=2
d=''
overwrite=''

# parse input arguments
while [[ $# > 0 ]]; do
	InArg="$1"
	case $InArg in
		-w)
			w=$2
			shift
			;;
		-t)
			t=$2
			shift
			;;
		-d)
			d='-d '
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
echo 'Submitting job for postprocessing.'
qsub -j y -N Postprocess -V -b y cd /projectnb/landsat/users/xjtang/documents/';' python -m VNRT.postprocess ${overwrite}${d}-w $w -t $t $ori $des
