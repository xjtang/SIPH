#!/bin/bash

# bash script to download data

# Input Arguments:
#   -s sensor V for VIIRS, M for MODIS
#   -c collection 5 or 6 if MODIS, 1 if VIIRS
#   -p product e.g. VNP09GA
#   -t tile h v
#   -y year
#   -d day, start stop
# 	-l login, username password
# 	-m method, ftp or http
#   des: destination

# default values
sensor=V
collection=1
product=VNP09GA
h=12
v=9
year=2017
dstart=0
dend=0
username=NA
password=NA
method=ftp

# parse input arguments
while [[ $# > 0 ]]; do

	InArg="$1"

	case $InArg in
		-s)
			sensor=$2
			shift
			;;
		-c)
			collection=$2
			shift
			;;
		-p)
			product=$2
			shift
			;;
		-t)
			h=$2
			v=$3
			shift
			shift
			;;
		-y)
			year=$2
			shift
			;;
		-d)
			dstart=$2
			dend=$3
			shift
			shift
			;;
		-l)
			username=$2
			password=$3
			shift
			shift
			;;
		-m)
			method=$2
			shift
			;;
		*)
			des=$1
			break
	esac

	shift

done

# run python script
if [ $method = "ftp" ]; then
	qsub -l eth_speed=10 -j y -N Download -V -b y cd /projectnb/landsat/users/xjtang/documents/';' python -m SIPH.tools.ftp_download -s $sensor -c $collection -p $product -t $h $v -y $year -d $dstart $dend $des
elif [ $method = "http" ]; then
	qsub -l eth_speed=10 -j y -N Download -V -b y cd /projectnb/landsat/users/xjtang/documents/';' python -m SIPH.tools.http_download -u $username -w $password -s $sensor -c $collection -p $product -t $h $v -y $year -d $dstart $dend $des
else
	echo 'unknown method'
fi
