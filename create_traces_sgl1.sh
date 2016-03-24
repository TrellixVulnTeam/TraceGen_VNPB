#!/bin/bash

# DEPRECATED DO NOT USE 

#####################################################
#Automating traces, throwaway script
#####################################################

parsec_dir=~/parsec-3.0
parsec_inst=amd64-linux.gcc-pthreads

sigil1_dir=~/Sigil1
sigil1_bin="$sigil1_dir/runsigil_and_gz.py --fair-sched=yes --tool=callgrind --separate-callers=100 --toggle-collect=main --cache-sim=yes --dump-line=no --drw-func=no --drw-events=yes --drw-splitcomp=100 --drw-intercepts=yes --drw-syscall=no --branch-sim=yes --separate-threads=yes --callgrind-out-file=callgrind.out.threads" 


trace_dir=~/synchrotraces/sigil1

# is parsec 3.0 raytrace appropriate?
parsec_apps=(blackscholes bodytrack facesim ferret fluidanimate swaptions vips x264)
parsec_kernels=(canneal streamcluster)

threads=(2 4 8 16)

#Creating the output directories

for i in ${threads[@]}; do
	for benchmark in ${parsec_apps[@]}; do
		mkdir -p $trace_dir/parsec/apps/$benchmark/${i}_threads/
	done
	for benchmark in ${parsec_kernels[@]}; do
		mkdir -p $trace_dir/parsec/kernels/$benchmark/${i}_threads/
	done
done


#Generating the SynchroTraceGen traces

simsize=simsmall

export TMPDIR=/dev/shm

for thr in ${threads[@]}; do
	NTHREADS=$thr

	for benchmark in ${parsec_apps[@]}; do

		pushd $trace_dir/parsec/apps/$benchmark/${thr}_threads/

		bench_dir="$parsec_dir/pkgs/apps/${benchmark}/inst/${parsec_inst}"

		command_out=command.txt

		inputs=$bench_dir/../../inputs/input_simsmall.tar

		if [ -e $inputs ]
		then
			tar -xf $inputs -C $bench_dir
		fi

		config=$bench_dir/../../parsec/${simsize}.runconf
		. ${config}
		executable="$bench_dir/${run_exec} ${run_args}"
		sigil_cmd="$sigil1_bin $executable"

		/bin/time -v $sigil_cmd 2>time.txt
		$sigil1_dir/tools/generate_pthread_file.py err.gz
		echo $sigil_cmd > $command_out

		popd
	done
	for benchmark in ${parsec_kernels[@]}; do

		pushd $trace_dir/parsec/kernels/$benchmark/${thr}_threads/

		bench_dir="$parsec_dir/pkgs/kernels/${benchmark}/inst/${parsec_inst}"

		command_out=command.txt

		inputs=$bench_dir/../../inputs/input_simsmall.tar

		if [ -e $inputs ]
		then
			tar -xf $inputs -C $bench_dir
		fi

		config=$bench_dir/../../parsec/${simsize}.runconf
		. ${config}
		executable="$bench_dir/${run_exec} ${run_args}"
		sigil_cmd="$sigil1_bin $executable"

		/bin/time -v $sigil_cmd 2>time.txt
		$sigil1_dir/tools/generate_pthread_file.py err.gz
		echo $sigil_cmd > $command_out

		popd
	done
done
