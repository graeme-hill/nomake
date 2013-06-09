#!/usr/bin/python

# Copyright (C) 2013 Graeme Hill
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal 
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in 
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os, re, subprocess, shutil, sys

SOURCE_DIRECTORY = 'src'
MODULES_DIRECTORY = 'src/modules'
RESOURCE_DIRECTORY = 'res'
LIB_DIRECTORY = 'lib'
INCLUDE_DIRECTORY = 'include'
OBJ_EXTENSIONS = ['o']
C_EXTENSIONS = ['c']
CPP_EXTENSIONS = ['C', 'cxx', 'cpp', 'CPP', 'CXX', 'cc', 'CC']
OBJC_EXTENSIONS = ['m', 'M']
OBJCPP_EXTENSIONS = ['mm', 'MM']
HEADER_EXTENSIONS = ['h', 'H', 'hh', 'HH', 'HPP', 'hpp', 'hxx', 'HXX']
SOURCE_EXTENSIONS = C_EXTENSIONS + CPP_EXTENSIONS + OBJC_EXTENSIONS + OBJCPP_EXTENSIONS
DEFAULT_COMPILER = 'clang++'
OBJ_DIR = 'obj'
APP_NAME = 'myapp'
BIN_DIR = 'bin'

class BuildOptions(object):
    def __init__(self):
        self.compiler = None
        self.modules = []
        self.get_help = False
        self.run = False
        self.clean = False

        def set_compiler(self, c): self.compiler = c
        def set_modules(self, m): self.modules = m
        def set_get_help(self, gh): self.get_help = gh
        def set_clean(self, c): self.clean = c
        def set_run(self, r): self.run = r

class Parameter(object):
    def __init__(self, long_name, short_name, description, action):
        self.long_name = long_name
        self.short_name = short_name
        self.description = description
        self.action = action

class Language(object):
    def __init__(self, name, extensions, precedence):
        self.name = name
        self.extensions = extensions
        self.precedence = precedence

class FileInfo(object):
    def __init__(self, path):
        self.path = normalize_path(path)
        self.timestamp = os.path.getmtime(path)

class BuildContext(object):
    def __init__(self, options):
        self.base_dir = '.'
        self.compiler = options.compiler
        self.modules = options.modules
        self.app_name = APP_NAME
        self.src_dir = join_paths(self.base_dir, SOURCE_DIRECTORY)
        self.obj_dir = join_paths(self.base_dir, OBJ_DIR)
        self.bin_dir = join_paths(self.base_dir, BIN_DIR)
        self.exe_path = join_paths(self.bin_dir, self.app_name)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def get_modules_for_target(self, target):
        return []

    def anything_changed_since_last_build(self, source_files):
        if os.path.exists(self.exe_path):
            last_build = os.path.getmtime(self.exe_path)
            for f in source_files:
                if f.timestamp >= last_build:
                    return True
            return False
        return True

    def find_files(self, directory, extensions):
        def is_included(fname):
            return directory != MODULES_DIRECTORY or fname in self.modules
        files = []
        if os.path.isdir(directory):
            for child in [join_paths(directory, f) for f in os.listdir(directory) if is_included(f)]:
                if os.path.isfile(child):
                    if child.split('.')[-1] in extensions:
                        files.append(FileInfo(child))
                else:
                    files += self.find_files(child, extensions)
        return files

    def parse_dep_line(self, dep_line):
        obj = dep_line[:dep_line.find(':')]
        sources = [normalize_path(path) for path in WHITESPACE.split(dep_line)[1:]]
        return (join_paths(self.obj_dir, obj), sources)

    def line_empty(self, line):
        return EMPTY_OR_WS.match(line) != None

    def get_dependencies(self, sources):
        cmd = [self.compiler, '-MM'] + [s.path for s in sources]
        print (cmd)
        outdata, errdata = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()
        output = outdata.decode('utf-8').replace('\\\n', '')
        return [self.parse_dep_line(line) for line in output.split('\n') if not self.line_empty(line)]

    def make_dir(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    def kill_dir(self, directory):
        if os.path.isdir(directory):
            shutil.rmtree(directory)

    def most_recent(self, files, timestamps):
        max_ts = None
        for f in files:
            ts = timestamps[f]
            if max_ts == None or ts > max_ts:
                max_ts = ts
        return max_ts

    def compile(self, obj_groups, src_timestamps, obj_timestamps):
        self.make_dir(self.obj_dir)
        for obj, sources in obj_groups:
            most_recent = self.most_recent(sources, src_timestamps)
            obj_name = obj[obj.rfind('/')+1:obj.rfind('.')]
            main_src = next(src for src in sources if src[src.rfind('/')+1:src.find('.')] == obj_name)
            if obj not in obj_timestamps or obj_timestamps[obj] <= most_recent:
                cmd = "%s -Wall -Werror -c %s -o %s" % (self.compiler, main_src, obj)
                print(cmd)
                if os.system(cmd) != 0:
                    return False
        return True

    def link(self, obj_groups):
        self.make_dir(self.bin_dir)
        objs = [obj for obj, sources in obj_groups]
        cmd = "%s -o %s %s" % (self.compiler, self.exe_path, ' '.join(objs))
        print(cmd)
        return os.system(cmd) == 0

    def build(self):
        print(self.__dict__)
        obj_files = self.find_files(self.obj_dir, OBJ_EXTENSIONS)
        src_files = self.find_files(self.src_dir, SOURCE_EXTENSIONS)
        header_files = self.find_files(self.src_dir, HEADER_EXTENSIONS)

        obj_timestamps = {o.path: o.timestamp for o in obj_files}
        src_timestamps = {s.path: s.timestamp for s in (src_files + header_files)}

        obj_groups = self.get_dependencies(src_files)
        if self.anything_changed_since_last_build(src_files + header_files):
            if self.compile(obj_groups, src_timestamps, obj_timestamps):
                if self.link(obj_groups):
                    return True
        else:
            return True
        return False

    def run(self):
        os.system(self.exe_path)

    def clean(self):
        self.kill_dir(self.obj_dir)
        self.kill_dir(self.bin_dir)

def invalid_args():
    print('Invalid arguments.\n')
    print_help()
    sys.exit()

def require_single_arg(values):
    if len(values) != 1:
        invalid_args()
    else:
        return values[0]

def normalize_path(path):
    return os.path.normpath(path)

def join_paths(a, b):
    return normalize_path(os.path.join(a, b))

def print_help():
    print('nomake - A really simple build system. Usage:\n')
    print('nomake.py [target] <options>\n')
    print('Options:\n')
    max_col_1_chars = 0
    for param_key in PARAMETERS_BY_LONG_NAME:
        max_col_1_chars = len(param_key) if len(param_key) > max_col_1_chars else max_col_1_chars
    for param_key in PARAMETERS_BY_LONG_NAME:
        param = PARAMETERS_BY_LONG_NAME[param_key]
        gap_size = max_col_1_chars - len(param_key)
        gap = ''.join([' '  for _ in range(gap_size)])
        print('    --%s (-%s) %s%s' % (param_key, param.short_name, gap, param.description))

def get_arg_info(args):
    params = {}
    targetName = None
    param_type = None
    for arg in args:
        if arg.startswith('--'):
            param_type = arg[2:]
            params[param_type] = []
        elif arg.startswith('-'):
            param_type = PARAMETERS_BY_SHORT_NAME[arg[1:]].long_name
            params[param_type] = []
        elif param_type == None:
            if targetName == None:
                targetName = arg
            else:
                invalid_args()
        else:
            params[param_type].append(arg)
    
    target = None if targetName == None else load_target_by_name(targetName)

    return (target, params)

def load_target_by_name(targetName):
    with open('./config.py', 'r') as configReader:
        config = eval(configReader.read())
    if not (targetName in config):
        fail('Target "%s" not found in config' % targetName)
    return config[targetName]

def parse_args(args):
    target, arg_dict = get_arg_info(args)
    opt = BuildOptions()
    for param_key in arg_dict:
        PARAMETERS_BY_LONG_NAME[param_key].action((opt, arg_dict[param_key]))
    if target != None:
        if len(opt.modules) == 0: opt.modules = target['modules']
        if opt.compiler == None: 
            if 'compiler' in target:
                opt.compiler = target['compiler']
            else:
                opt.compiler = None
    return opt

# Config
PARAMETERS = [
    Parameter(
        long_name = 'modules',
        short_name = 'm',
        description = 'List of modules to include in build.',
        action = lambda opt, values: opt.set_modules(values)),
    Parameter(
        long_name = 'compiler',
        short_name = 'c',
        description = 'Specific compiler to use on all source files.',
        action = lambda opt, values: opt.set_compiler(require_single_arg(values))),
    Parameter(
        long_name = 'help',
        short_name = 'h',
        description = 'Display help text.',
        action = lambda opt, values: opt.set_get_help(True)),
    Parameter(
        long_name = 'clean',
        short_name = 'C',
        description = 'Delete previous build output.',
        action = lambda opt, values: opt.set_clean(True)),
    Parameter(
        long_name = 'run',
        short_name = 'r',
        description = 'Run program after compiling.',
        action = lambda opt, values: opt.set_run(True))
]
PARAMETERS_BY_LONG_NAME = {p.long_name: p for p in PARAMETERS}
PARAMETERS_BY_SHORT_NAME = {p.short_name: p for p in PARAMETERS}

# Constant regular expressions
EMPTY_OR_WS = re.compile('^\\s*$')
WHITESPACE = re.compile('\\s+')

if __name__ == '__main__':
    options = parse_args(sys.argv[1:])
    with BuildContext(options) as context:
        if options.get_help:
            print_help()
        elif options.clean:
            context.clean()
        elif context.build() and options.run:
            context.run()
