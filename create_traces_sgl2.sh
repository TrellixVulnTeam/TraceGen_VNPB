#!/bin/bash

# DEPRECATED DO NOT USE

#####################################################
#Automating traces, throwaway script
#####################################################

parsec_dir=~/parsec-3.0
parsec_inst=amd64-linux.gcc-pthreads

sigil2_bin=~/Sigil2/build/bin/sigil2

trace_dir=~/synchrotraces/sigil2/valgrind

# all the parsec
parsec_apps=(blackscholes bodytrack facesim ferret fluidanimate swaptions vips x264)
parsec_kernels=(canneal streamcluster)

splash2x_apps=()

threads=(2 4 8 16)

# build required apps
#for benchmark in ${parsec_apps[@]}; do
#	$parsec_dir/bin/parsecmgmt -a build -c gcc-pthreads -p $benchmark
#done
#for benchmark in ${parsec_kernels[@]}; do
#	$parsec_dir/bin/parsecmgmt -a build -c gcc-pthreads -p $benchmark
#done

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
		## jump into benchmark dir
		pushd $parsec_dir/pkgs/apps/${benchmark}/inst/${parsec_inst}

		## prepare the inputs

		#sigil_out=sigil2.txt
		#command_out=command.txt
		#out_dir=$trace_dir/parsec/apps/$benchmark/${thr}_threads/

		#config=../../parsec/${simsize}.runconf
		#. ${config}
		#executable="${run_exec} ${run_args}"
		#sigil_args="--frontend=valgrind --backend=stgen --exec=\"$executable\" > $sigil_out 2>&1"
		#full_cmd="/bin/time -v $sigil2_bin  $sigil_args"
		#eval $full_cmd
	
		#echo $full_cmd > $command_out

		#mv sigil.events.out-* ${out_dir}
		#mv sigil.pthread.out ${out_dir}
		#mv $sigil_out $out_dir
		mv $command_out $out_dir

		popd
	done
	for benchmark in ${parsec_kernels[@]}; do
		# jump into benchmark dir
		pushd $parsec_dir/pkgs/kernels/${benchmark}/inst/${parsec_inst}

		# prepare the inputs

		sigil_out=sigil2.txt
		command_out=command.txt
		out_dir=$trace_dir/parsec/kernels/$benchmark/${thr}_threads/

		config=../../parsec/${simsize}.runconf
		. ${config}
		executable="${run_exec} ${run_args}"
		sigil_args="--frontend=valgrind --backend=stgen --exec=\"$executable\" > $sigil_out 2>&1"
		full_cmd="/bin/time -v $sigil2_bin  $sigil_args"
		eval $full_cmd

		echo $full_cmd > $command_out

		mv sigil.events.out-* ${out_dir}
		mv sigil.pthread.out ${out_dir}
		mv $sigil_out $out_dir
		mv $command_out $out_dir

		popd
	done
done
