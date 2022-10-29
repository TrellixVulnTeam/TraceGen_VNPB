"""
    parsec_benchmarks
    ~~~~~~~~~~~~~~~~~

    Configures parsec benchmarks for automation.
"""
from collections import namedtuple
BenchmarkExec = namedtuple("BenchmarkExecutable",
                           "binary args directory threads")


APPS = ['blackscholes', 'bodytrack', 'facesim', 'ferret',
        'fluidanimate', 'swaptions', 'vips', 'x264']

KERNELS = ['canneal', 'streamcluster']


def find_dir(root, name):
    import os
    for dirname, dirnames, filenames in os.walk(root):
        for dir in dirnames:
            if name == dir:
                return os.path.join(dirname, dir)


class ParsecBenchmark(object):
    thread_arg = "${NTHREADS}"

    def __init__(self, name, parsec_path, dataset, threads=[1]):
        """Prepare a parsec benchmark and access associated commands.

        Parameters
        ----------
        name : str
            Benchmark name
        parsec_path : str
            Path to parsec-3.0 directory
        dataset : str
            Dataset size to run with benchmark; e.g. 'simsmall', 'native'
        threads : arr
            Each array entry is a benchmark configuration
            specifying the number of threads to run
        """
        is_app = name in APPS
        is_kernel = name in KERNELS
        if not is_app and not is_kernel:
            raise ValueError("unrecognized benchmark")

        self.name = name
        self.parsec_path = parsec_path
        self.dataset = dataset
        self.threads = threads
        self.benchmark_path = None
        self.config_path = None
        self.input_path = None
        self.binary_path = None
        self.binary = None
        self.args = None
        self.suite = None
        self.configured = False

    def _configure(self, dataset=None):
        if dataset is None:
            dataset = self.dataset

        self.benchmark_path = find_dir(self.parsec_path, self.name)
        self.binary_path = find_dir(self.benchmark_path, "bin")
        self.config_path = find_dir(self.benchmark_path, "parsec")
        self.input_path = find_dir(self.benchmark_path, "inputs")
        # input path (may not exist for some benchmarks)

        config_file = self.config_path + "/" + dataset + ".runconf"
        with open(config_file) as config:
            for line in config:
                if "=" in line:
                    key, val = line.rstrip().replace('"', '').split("=")
                    if key == "run_exec":
                        self.binary = val
                    elif key == "run_args":
                        self.args = val

        if self.input_path:
            import tarfile
            filename = self.input_path + "/input_" + dataset + ".tar"
            with tarfile.open(filename) as tar:
                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner=numeric_owner) 
                    
                
                safe_extract(tar)
                tar.close()

        self.configured = True

    def generate_suite(self, dataset=None, threads=None):
        if dataset is None:
            dataset = self.dataset

        if threads is None:
            threads = self.threads

        self._configure()

        self.suite = []
        for thread in threads:
            executable = BenchmarkExec(binary=self.binary,
                                       args=self.args.replace(
                                           self.thread_arg,
                                           str(thread)),
                                       directory=self.binary_path.rstrip('bin'),
                                       threads=thread)
            self.suite.append(executable)
        return self.suite

    def compile(self):
        import subprocess
        import shlex
        """Compile the benchmark.

        Use parsec's builtin management utility for compilation.
        The gcc-pthreads compiler configuration is hardcoded
        for multithreaded benchmarks
        """
        parsecmgmt = self.parsec_path + "/bin/parsecmgmt"
        action = "-a build"
        config = "-c gcc-pthreads"
        package = "-p " + self.name
        command = " ".join([parsecmgmt, action, config, package])
        ret = subprocess.call(shlex.split(command))

        if not ret == 0:
            raise RuntimeError("Benchmark failed to compile")


class ParsecConfig(object):

    def __init__(self, path, dataset, threads=[1]):
        """Configure parsec benchmarks for execution.

        The parsec benchmarks are compiled and inputs are prepared for the
        configured dataset.  A set of commands for the given benchmark are
        returned that can be executed in place.

        This is mostly useful for automation of benchmarks or generation
        of other scripts.

        Parameters
        ----------
        parsec_path : str
            Path to parsec-3.0 directory
        dataset : str
            Dataset size to run with benchmark; e.g. 'simsmall', 'native'
        threads : arr
            Each array entry is a benchmark configuration
            specifying the number of threads to run
        """
        if dataset not in ['test', 'simsmall', 'simmedium',
                           'simlarge', 'native']:
            raise ValueError("invalid dataset")

        self.parsec_path = path
        self.dataset = dataset
        self.threads = threads

    def blackscholes(self):
        return ParsecBenchmark("blackscholes", self.parsec_path, self.dataset,
                               self.threads)

    def bodytrack(self):
        return ParsecBenchmark("bodytrack", self.parsec_path, self.dataset,
                               self.threads)


class blackscholes(object):

    def __init__(self):
        return
