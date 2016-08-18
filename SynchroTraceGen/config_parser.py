#!/usr/bin/python2

# TODO this file requires CLEANUP

import os
import time
import shlex
import subprocess
import tempfile
from ConfigParser import ConfigParser
from ParsecGenerator import ParsecGenerator
from functools import partial
from argparse import ArgumentParser
from shutil import rmtree
from glob import glob
from os.path import abspath, expanduser, join as joinpath
from os import chdir, getcwd


def run_sigil2_vg_stgen(sigil_path, outdir, cmdline):
    sigil_command = joinpath(sigil_path, 'bin/sigil2')
    sigil_args = ('--frontend=dynamorio' +
                  ' --start-func=__parsec_roi_begin' +
                  ' --stop-func=__parsec_roi_end')
    sigil_args += ' --backend=stgen -o ' + outdir
    sigil_args += ' --executable=' + cmdline

    # get time and memory usage stats
    run = '/bin/time -v ' + sigil_command + ' ' + sigil_args
    print(run)

    sigil_res = subprocess.check_output(shlex.split(run),
                                        stderr=subprocess.STDOUT)
    log = run + '\n'
    log += sigil_res.decode('utf-8')

    return log


def run_sigil1(sigil_path, outdir, cmdline):
    sigil_command = joinpath(sigil_path, 'valgrind-3.10.1/vg-in-place')
    sigil_args = ('--fair-sched=yes ' +
                  '--tool=callgrind ' +
                  '--separate-callers=100 ' +
                  '--toggle-collect=main ' +
                  '--cache-sim=yes ' +
                  '--dump-line=no ' +
                  '--drw-func=no ' +
                  '--drw-events=yes ' +
                  '--drw-splitcomp=100 ' +  # default in Sigil2
                  '--drw-intercepts=yes ' +
                  '--drw-syscall=no ' +
                  '--branch-sim=yes ' +
                  '--separate-threads=yes ' +
                  '--callgrind-out-file=callgrind.out.threads ')
    sigil_args += cmdline

    # get time and memory usage stats
    run = '/bin/time -v ' + sigil_command + ' ' + sigil_args

    env = os.environ.copy()
    env['LD_PRELOAD'] = joinpath(sigil_path, 'tools/wrapper.so')
    print(run)
    sigil_p = subprocess.Popen(shlex.split(run),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               env=env)

    sigil_out = sigil_p.communicate()[0]
    if sigil_p.returncode != 0:
        errmsg = '-----------------------------------------------\n'
        errmsg += 'ERROR: ' + run + '\n'
        errmsg += 'RETURN CODE: ' + str(sigil_p.returncode) + '\n'
        errmsg += '-----------------------------------------------\n'
        errmsg += sigil_out
        return errmsg

    gzip_cmd = 'gzip '
    gzip_cmd += ' '.join(glob('sigil.events.out-*'))
    subprocess.check_call(shlex.split(gzip_cmd))

    mv_cmd = 'mv '
    mv_cmd += ' '.join(glob('sigil.events.out-*'))
    mv_cmd += ' ' + outdir
    subprocess.check_call(shlex.split(mv_cmd))

    log = (run + '\n\n' + gzip_cmd + '\n\n' + mv_cmd + '\n\n')
    log += sigil_out
    return log


def run_sigil(config_file, version, outdir):
    parser = ConfigParser()
    parser.read(config_file)
    if version == 1:
        sigil_path = parser.get('general', 'sigil_one_path')
        sigil_path = abspath(expanduser(sigil_path))
        runsigil = partial(run_sigil1, sigil_path)
    elif version == 2:
        sigil_path = parser.get('general', 'sigil_two_path')
        sigil_path = abspath(expanduser(sigil_path))
        runsigil = partial(run_sigil2_vg_stgen, sigil_path)
    else:
        print('Invalid sigil version {}'.format(version))
        return

    try:
        # work in a temp dir
        tmpdir = tempfile.mkdtemp()
        origdir = getcwd()
        chdir(tmpdir)

        for bench in ParsecGenerator.generate(config_file, ['apps']):
            # run sigil, and log time and all output
            print bench
            pass
            outdir_bench = joinpath(outdir,
                                    bench.config, bench.size, bench.threads)
            try:
                os.makedirs(outdir_bench)
            except OSError as e:  # do nothing if directory already exists
                if e.errno == 17:  # directory already exists
                    pass
                else:
                    raise e

            start_time = time.time()
            log = runsigil(outdir_bench, bench.cmdline)
            print log
            total_time = time.time() - start_time
            with open(joinpath(outdir_bench, 'log.txt'), 'w+') as log_file:
                log_file.write('--- {} seconds ---\n\n'.format(total_time))
                log_file.write(log)
    finally:
        # clean up
        chdir(origdir)
        rmtree(tmpdir)


def main():
    parser = ArgumentParser()

    parser.add_argument('-p', action='store', required=True,
                        dest='config_path', help='Path to config file')

    parser.add_argument('-o', action='store', dest='output_path', default='.',
                        help="Default is '.'")

    parser.add_argument('-v', action='store', dest='sigil_version',
                        required=True, type=int, choices=[1, 2],
                        help="'1' for Sigil1, '2' for Sigil2")

    args = parser.parse_args()
    config_file = abspath(expanduser(args.config_path))
    sigil_version = args.sigil_version
    out_dir = abspath(expanduser(args.output_path))

    run_sigil(config_file, sigil_version, out_dir)

if __name__ == '__main__':
    main()
