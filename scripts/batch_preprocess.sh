#!/bin/bash

# bash script to submit jobs for preprocessing

# Input Arguments:
#   -p searching pattern
#   -n number of jobs
#   --overwrite overwrite
#   ori: origin
#   des: destination

# default values
njob=1
overwrite=0
pattern=VNP09GA*h5

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
      qsub -N VNRT_$i ./preprocess.sh -p $pattern -b $i $njob $ori $des
    elif [ $overwrite = 1 ]; then
      qsub -N VNRT_$i ./preprocess.sh --overwrite -p $pattern -b $i $njob $ori $des
    fi
done
