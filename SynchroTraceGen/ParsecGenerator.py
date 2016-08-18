#!/usr/bin/python

# TODO this file requires CLEANUP

import os
import re
import shutil
import tarfile
from os.path import abspath, expanduser, join as joinpath
from ConfigParser import ConfigParser
from collections import namedtuple


class ParsecGenerator(ConfigParser):
    BenchmarkRun = namedtuple('BenchmarkRun',
                              'config size threads cmdline')

    CONFIG_SIZE = 'sizes'
    CONFIG_TAR = 'tarball'
    CONFIG_THREAD = 'threads'

    def __init__(self, config_file):
        """Sets up parsec benchmark generation

        Parameters
        ----------
        config_file : str
            A valid parsec.cfg file
        """
        ConfigParser.__init__(self)

        if not self.read(config_file):
            raise IOError('Cannot open config file \'{}\''.format(config_file))

        parsec_path = self.get('general', 'parsec_path')
        if parsec_path:
            self.parsec_path = abspath(expanduser(parsec_path))

    def _get_parsec_subpath(self, benchmark, subpath_name):
        """ Finds a subpath for a 'parsec' benchmark.

        Looks in 'parsec' specific directory for a benchmark subpath.
        The user should not use this function if finding a directory
        or file for a splash2, or splash2x benchmark.
        """
        parsec_path = joinpath(self.parsec_path, 'pkgs')
        for dirname, subdirlist, filelist in os.walk(parsec_path):
            if benchmark in dirname and subpath_name in subdirlist:
                return joinpath(dirname, subpath_name)
        raise Exception('Could not find subdir \'' + subpath_name + '\'' +
                        ' for benchmark \'' + benchmark + '\'')

    def _valid_option(self, config, option):
        if not self.has_option(config, option):
            print('[' + config + ']' + ' missing (' + option + ') option')
            return False
        else:
            return True

    def _valid(self, config):
        if not self.has_section(config):
            print('[' + config + ']' + ' could not be located in config file')
            return False
        elif not self._valid_option(config, self.CONFIG_SIZE):
            return False
        elif not self._valid_option(config, self.CONFIG_THREAD):
            return False
        else:
            return True

    def _benchmark_configs(self, config, benchmark):
        # missing config info check
        if not self._valid(config):
            return

        # data sets for different size configs
        sizes = self.get(config, self.CONFIG_SIZE).split()
        if self.has_option(config, self.CONFIG_TAR):
            required = self.get(config, self.CONFIG_TAR)
            if required.lower() == 'true':
                path = self._get_parsec_subpath(benchmark, 'inputs')
                for f in map(lambda s: 'input_' + s + '.tar', sizes):
                    shutil.copy(joinpath(path, f), '.')
                    tar = tarfile.open(f)
                    tar.extractall()
                    tar.close()
                    os.remove(f)
            elif required.lower() != 'false':
                print('Unexpected \'tarball\' value')

        # generate commandline based on thread/size configs
        bin_path = self._get_parsec_subpath(benchmark, 'bin')
        config_path = self._get_parsec_subpath(benchmark, 'parsec')
        threads = self.get(config, self.CONFIG_THREAD).split()
        for size in sizes:
            config_file = joinpath(config_path, size + '.runconf')
            with open(config_file) as f:
                lines = f.readlines()
                run_exec = [line for line in lines if 'run_exec' in line][0]
                run_args = [line for line in lines if 'run_args' in line][0]
            if not run_exec or not run_args:
                raise Exception('Could not find run config in *.runconf file ' +
                                config_file)

            run_exec = re.findall(r'\"(.+?)\"', run_exec)[0]
            if run_exec.startswith('bin/'):
                run_exec = run_exec[len('bin/'):]
            run_exec = joinpath(bin_path, run_exec)

            run_args = re.findall(r'\"(.+?)\"', run_args)[0]
            run_cmd = run_exec + ' ' + run_args
            for thread in threads:
                cmdline = run_cmd.replace('${NTHREADS}', thread)
                yield self.BenchmarkRun(config, size, thread, cmdline)

    def _generate(self, section_keys):
        """A generator for parsec benchmarks available in config

        Each matching section will have the required inputs copied to the cwd.

        A named tuple for the benchmark, containing the full command line,
        will be returned upon each iteration.

        All benchmarks whose '[section]' has ALL strings listed in
        'section_keys' will be generated.
        For example, given a '[apps.blackscholes]' section exists:
            my_parsec_generator.generate(['apps']) # matches ALL apps
            my_parsec_generator.generate(['blackscholes']) # only matches bs
        This is to differentiate between benchmarks that exist in both
        splash2 and parsec.

        Parameters
        ----------
        section_keys : [str]
            Sections in config will be searched to match ALL strings in
            'section_keys'.
        """
        if type(section_keys) is not list:
            raise Exception('param must be list')

        matches = []
        for key in section_keys:
            match = filter(lambda s: key in s, self.sections())
            if not matches:
                matches = match
            else:
                matches = list(set(matches) & set(match))

        for benchmark_config in matches:
            benchmark = benchmark_config
            # Parse out just the benchmark name, e.g. [apps.blackscholes]
            if '.' in benchmark_config:
                benchmark = benchmark_config.split('.')[1]
            for benchmarkrun in self._benchmark_configs(benchmark_config,
                                                        benchmark):
                yield benchmarkrun

    @staticmethod
    def generate(config_file, sections):
        generator = ParsecGenerator(config_file)

        if sections:
            for benchmarkrun in generator._generate(sections):
                yield benchmarkrun
