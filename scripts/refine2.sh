#!/bin/bash

# bash script to refine classification results

# Input Arguments:
#		--overwrite overwrite
#		ori: origin
#   lc: MODIS land cover stack
#		vcf: MODIS vcf stack
#		des: destination

# default values
overwrite=''

# parse input arguments
while [[ $# > 0 ]]; do
	InArg="$1"
	case $InArg in
		--overwrite)
			overwrite='--overwrite '
			;;
		*)
      ori=$1
      lc=$2
			vcf=$3
			des=$4
			break
	esac
	shift
done

# submit job
echo 'Submitting job to refine classification results'
qsub -l mem_total=94G -j y -N Refine -V -b y cd /projectnb/landsat/users/xjtang/documents/';' python -m SIPH.models.chart.refine2 ${overwrite} $ori $lc $vcf $des
