#!/usr/bin/python

from argparse import ArgumentParser
from parsec_benchmarks import ParsecConfig

import time
import os
import subprocess
import shlex
from glob import glob


def sigil2_command(output_path, executable, sigil2_path):
    """Runs sigil2 and returns a console log

    Parameters
    ----------
    output_path : str
        Location for sigil.events.out-*.gz files
    executable : str
        The benchmark executable
    sigil_path : str
        Path to bin/sigil2
    """
    sigil2_backend = '--backend=stgen -o ' + output_path
    sigil2_exec = '--executable=' + executable
    sigil2_bin = sigil2_path.rstrip('/') + '/bin/sigil2'
    sigil2_cmd = sigil2_bin + ' ' + sigil2_backend + ' ' + sigil2_exec

    # get time and memory usage stats
    run = '/bin/time -v ' + sigil2_cmd

    sigil_res = subprocess.check_output(shlex.split(run),
                                        stderr=subprocess.STDOUT)
    log = sigil2_cmd + '\n'
    log += sigil_res.decode('utf-8')

    return log


def sigil1_command(output_path, executable, sigil_path):
    """Runs sigil1 and returns a console log

    Parameters
    ----------
    output_path : str
        Location for sigil.events.out-*.gz files
    executable : str
        The benchmark executable
    sigil_path : str
        Path to sigil1 dir
    """
    vg_script = (sigil_path.rstrip('/') +
                 '/valgrind-3.10.1/vg-in-place ')
    sigil_cmd = (vg_script +
                 '--fair-sched=yes ' +
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
                 '--callgrind-out-file=callgrind.out.threads ' +
                 executable)

    # get time and memory usage stats
    run = '/bin/time -v ' + sigil_cmd

    env = os.environ.copy()
    env['LD_PRELOAD'] = sigil_path + '/tools/wrapper.so'
    sigil_p = subprocess.Popen(shlex.split(run),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               env=env)

    sigil_out = sigil_p.communicate()[0]
    if sigil_p.returncode != 0:
        raise subprocess.CalledProcessError(sigil_p.returncode, run)

    gzip_cmd = 'gzip '
    gzip_cmd += ' '.join(glob('sigil.events.out-*'))
    subprocess.check_call(shlex.split(gzip_cmd))

    mv_cmd = 'mv '
    mv_cmd += ' '.join(glob('sigil.events.out-*'))
    mv_cmd += ' ' + output_path
    subprocess.check_call(shlex.split(mv_cmd))

    log = (sigil_cmd + '\n\n' + gzip_cmd + '\n\n' + mv_cmd + '\n\n')
    log += sigil_out

    return log


def main():
    """ Setup and run all benchmarks.

    The benchmarks are run directly instead of through parsec's management
    function to avoid the cost of that indirection.
    """
    parser = ArgumentParser()

    parser.add_argument('-p', action='store', required=True,
                        dest='parsec_path', help='Path to parsec-3.0')

    parser.add_argument('-s', action='store', required=True,
                        dest='sigil_path',
                        help=('If Sigil{1}, this is the top Sigil1 dir, ' +
                              'else if Sigil{2}, this is the path to ' +
                              'bin/sigil2'))

    parser.add_argument('-o', action='store', dest='output_path', default='.',
                        help="Default is '.'")

    parser.add_argument('-v', action='store', dest='sigil_version',
                        required=True, type=int, choices=[1, 2],
                        help="'1' for Sigil1, '2' for Sigil2")

    args = parser.parse_args()
    output_path = os.path.abspath(args.output_path)

    # hardcoded defaults
    dataset = 'simmedium'
    threads = [1]  # , 2, 4, 8, 16]
    parsec = ParsecConfig(args.parsec_path, dataset, threads)

    # generate command suite
    suite = []
    suite.append(parsec.blackscholes())
    suite.append(parsec.bodytrack())

    """
    Might fill up current working directory with temporary input/output files.
    Change to a temp working directory and delete afterwards
    """
    now = str(int(time.time()))
    wd = '.trace_env_' + now
    os.makedirs(wd)
    os.chdir(wd)

    # generate traces
    for benchmark in suite:
        for executable in benchmark.generate_suite():

            benchmark_command = (executable.directory.rstrip('/') + '/' +
                                 executable.binary)
            if not os.path.exists(benchmark_command):
                benchmark.compile()
                if not os.path.exists(benchmark_command):
                    raise IOError(benchmark_command + ' does not exist.')

            # OUTPUT_PATH/PARSEC_SUBDIR/N_THREADS/SIGIL_
            output = (output_path.rstrip('/') +
                      benchmark.benchmark_path.replace(os.path.expanduser('~'),
                                                       '') +
                      '/' + str(executable.threads) + '_threads' + '/' +
                      'sigil_' + str(args.sigil_version))

            try:
                os.makedirs(output)
            except OSError as e:  # do nothing if directory already exists
                if e.errno == 17:  # directory already exists
                    pass
                else:
                    raise e

            start_time = time.time()
            if args.sigil_version == 1:
                log = sigil1_command(output,
                                     benchmark_command + ' ' + executable.args,
                                     args.sigil_path)
            elif args.sigil_version == 2:
                log = sigil2_command(output,
                                     benchmark_command + ' ' + executable.args,
                                     args.sigil_path)
            total_time = time.time() - start_time

            with open(output + '/log.txt', 'w+') as log_file:
                log_file.write('--- {} seconds ---\n\n'.format(total_time))
                log_file.write(log)

    # clean up
    os.chdir('..')
    import shutil
    shutil.rmtree(wd)


if __name__ == '__main__':
    main()
