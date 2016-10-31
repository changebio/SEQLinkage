#!/usr/bin/python2.7
# Copyright (c) 2013 - 2014, Gao Wang <gaow@uchicago.edu> and Di Zhang <di.zhang@bcm.edu>
# GNU General Public License (http://www.gnu.org/licenses/gpl.html)
from . import VERSION
import sys, os, subprocess, shutil, glob, shlex, urlparse, re, hashlib, tempfile
from cStringIO import StringIO
from contextlib import contextmanager
from multiprocessing import Pool, Process, Queue, Lock, Value, cpu_count
import itertools
from collections import OrderedDict, defaultdict, Counter
from shutil import rmtree as remove_tree
from distutils.file_util import copy_file
from zipfile import ZipFile

# from distutils.dir_util import mkpath
def mkpath(directory):
    '''Have to use system mkdir here because python2.7's mkpath is currently faulty!'''
    os.system('mkdir -p {}'.format(directory))

###
# Global variables
###
class Environment:
    def __init__(self):
        self.__width_cache = 1
        # About the program
        self.proj = "SEQLinkage"
        self.prog = 'seqlink'
        self.version = VERSION
        # Runtime support
        self.resource_dir = os.path.expanduser('~/.{}'.format(self.proj))
        self.resource_bin = os.path.join(self.resource_dir, 'bin')
        self.cache_dir = os.path.join(os.getcwd(), 'cache')
        self.tmp_dir = self.__mktmpdir()
        self.tmp_cache = os.path.join(self.tmp_dir, 'CACHE')
        self.path = {'PATH':"{}:{}".format(self.resource_bin, os.environ["PATH"])}
        self.debug = False
        self.quiet = False
        # File contents
        self.build = 'hg19'
        self.delimiter = " "
        self.ped_missing = ['0', '-9'] + ['none', 'null', 'na', 'nan', '.']
        self.trait = 'binary'
        self.prephased = False
        # Input & output options
        self.output = 'LINKAGE'
        self.outdir = 'LINKAGE'
        self.tmp_log = os.path.join(self.tmp_dir, "clog." + self.output)
        # Multiprocessing counters
        self.batch = 50
        self.lock = Lock()
        self.total_counter = Value('i',0)
        self.success_counter = Value('i',0)
        self.null_counter = Value('i',0)
        self.trivial_counter = Value('i',0)
        self.chperror_counter = Value('i',0)
        self.variants_counter = Value('i',0)
        self.triallelic_counter = Value('i',0)
        self.commonvar_counter = Value('i',0)
        self.mendelerror_counter = Value('i',0)
        self.recomb_counter = Value('i',0)
        self.format_counter = Value('i',0)
        self.run_counter = Value('i',0)
        self.skipped_counter = Value('i',0)
        self.makeped_counter = Value('i',0)
        self.pedcheck_counter = Value('i',0)
        self.unknown_counter = Value('i',0)
        self.mlink_counter = Value('i',0)

    def __mktmpdir(self, where = None):
        class LockedTempDir(str):
            def __init__(self, path):
                self = path
                open(os.path.join(self, '.lock'), 'a').close()

            def __del__(self):
                try:
                    os.remove(os.path.join(self, '.lock'))
                except:
                    pass

        if where in [None, 'None', '']:
            where = tempfile.gettempdir()
        else:
            where = os.path.expanduser(where)
        if os.path.isdir(where) and ((not os.access(where, os.R_OK)) or (not os.access(where, os.W_OK))):
            self.error('Cannot set temporary directory to directory {} because '.format(where) + \
                       'it is not readable or writable.', exit = True)
        pattern = re.compile(r'{}_tmp_*(.*)'.format(self.proj))
        for fn in os.listdir(where):
            if pattern.match(fn) and not os.path.isfile(os.path.join(where, fn, '.lock')):
                try:
                    remove_tree(os.path.join(where, fn))
                except:
                    pass
        tmp = LockedTempDir(tempfile.mkdtemp(prefix='{}_tmp_'.format(self.proj), dir = where))
        mkpath(os.path.join(tmp, 'CACHE'))
        return tmp

    def ResetTempdir(self, path = None):
        self.tmp_dir = self.__mktmpdir(path)
        self.tmp_cache = os.path.join(self.tmp_dir, 'CACHE')
        self.tmp_log = os.path.join(self.tmp_dir, "clog." + self.output)
            
    def error(self, msg = None, show_help = False, exit = False):
        if msg is None:
            sys.stderr.write('\n')
            return
        if type(msg) is list:
            msg = ' '.join(map(str, msg))
        else:
            msg = str(msg)
        start = '\n' if msg.startswith('\n') else ''
        end = '\n' if msg.endswith('\n') else ''
        msg = msg.strip()
        sys.stderr.write(start + "\033[1;40;33mERROR: {}\033[0m\n".format(msg) + end)
        if show_help:
            self.log("Type '{} -h' for help message".format(env.prog))
            sys.exit()
        if exit:
            sys.exit()
        
    def log(self, msg = None, flush=False):
        if self.debug or self.quiet:
            return
        if msg is None:
            sys.stderr.write('\n')
            return
        if type(msg) is list:
            msg = ' '.join(map(str, msg))
        else:
            msg = str(msg)
        start = "{0:{width}}".format('\r', width = self.__width_cache + 10) + "\r" if flush else ''
        end = '' if flush else '\n'
        start = '\n' + start if msg.startswith('\n') else start
        end = end + '\n' if msg.endswith('\n') else end
        msg = msg.strip()
        sys.stderr.write(start + "\033[1;40;32mMESSAGE: {}\033[0m".format(msg) + end)
        self.__width_cache = len(msg)

env = Environment()

###
# Utility function / classes
###

class StdoutCapturer(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        sys.stdout = self._stdout

@contextmanager
def stdoutRedirect(to=os.devnull):
    '''
    import os

    with stdoutRedirect(to=filename):
        print("from Python")
        os.system("echo non-Python applications are also supported")
    '''
    fd = sys.stdout.fileno()

    ##### assert that Python and C stdio write using the same file descriptor
    ####assert libc.fileno(ctypes.c_void_p.in_dll(libc, "stdout")) == fd == 1

    def _redirect_stdout(to):
        sys.stdout.close() # + implicit flush()
        os.dup2(to.fileno(), fd) # fd writes to 'to' file
        sys.stdout = os.fdopen(fd, 'w') # Python writes to fd

    with os.fdopen(os.dup(fd), 'w') as old_stdout:
        with open(to, 'a') as file:
            _redirect_stdout(to=file)
        try:
            yield # allow code to be run with the redirected stdout
        finally:
            _redirect_stdout(to=old_stdout) # restore stdout.
                                            # buffering and flags such as
                                            # CLOEXEC may be different

#http://stackoverflow.com/a/13197763, by Brian M. Hunt
class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = newPath

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)

def runCommand(cmd, instream = None, msg = '', upon_succ = None, show_stderr = False, return_zero = True):
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    popen_env = os.environ.copy()
    popen_env.update(env.path)
    try:
        tc = subprocess.Popen(cmd, stdin = subprocess.PIPE,
                              stdout = subprocess.PIPE, stderr = subprocess.PIPE,
                              env=popen_env)
        if instream:
            if sys.version_info.major == 3:
                instream = instream.encode(sys.getdefaultencoding())
            out, error = tc.communicate(instream)
        else:
            out, error = tc.communicate()
        if sys.version_info.major == 3:
            out = out.decode(sys.getdefaultencoding())
            error = error.decode(sys.getdefaultencoding())
        if return_zero:
            if tc.returncode < 0:
                raise ValueError ("Command '{0}' was terminated by signal {1}".format(cmd, -tc.returncode))
            elif tc.returncode > 0:
                raise ValueError ("{0}".format(error))
        if error.strip() and show_stderr:
            env.log(error)
    except OSError as e:
        raise OSError ("Execution of command '{0}' failed: {1}".format(cmd, e))
    # everything is OK
    if upon_succ:
        # call the function (upon_succ) using others as parameters.
        upon_succ[0](*(upon_succ[1:]))
    return out, error

class CMDWorker(Process):
    def __init__(self, queue):
        Process.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            try:
                cmd = self.queue.get()
                if cmd is None:
                    break
                else:
                    runCommand(cmd)
            except KeyboardInterrupt:
                break
            
def runCommands(cmds, ncpu):
    try:
        jobs = []
        queue = Queue()
        for i in cmds:
            queue.put(i)
        for i in range(ncpu):
            p = CMDWorker(queue)
            p.start()
            jobs.append(p)
            queue.put(None)
        for j in jobs:
            j.join()
    except KeyboardInterrupt:
        raise ValueError('Commands terminated!')

#utils that allow lambda function in mutilprocessing map
#http://stackoverflow.com/a/16071616 by klaus-se
def parmap(f, X, nprocs = cpu_count()):
    def spawn(f):
        def fun(q_in,q_out):
            while True:
                i,x = q_in.get()
                if i is None:
                    break
                q_out.put((i,f(x)))
        return fun
    #
    q_in   = Queue(1)
    q_out  = Queue()
    proc = [Process(target=spawn(f),args=(q_in,q_out)) for _ in range(nprocs)]
    for p in proc:
        p.daemon = True
        p.start()
    sent = [q_in.put((i,x)) for i,x in enumerate(X)]
    [q_in.put((None,None)) for _ in range(nprocs)]
    res = [q_out.get() for _ in range(len(sent))]
    [p.join() for p in proc]
    return [x for i,x in sorted(res)]

def downloadURL(URL, dest_dir, quiet = True, mode = None, force = False):
    if not os.path.isdir(dest_dir):
        mkpath(dest_dir)
    filename = os.path.split(urlparse.urlsplit(URL).path)[-1]
    dest = os.path.join(dest_dir, filename)
    if os.path.isfile(dest):
        if force:
            os.remove(dest)
        else:
            return
    # use wget
    try:
        # for some strange reason, passing wget without shell=True can fail silently.
        p = subprocess.Popen('wget {} -O {} {}'.format('-q' if quiet else '', dest, URL), shell=True)
        ret = p.wait()
        if ret == 0 and os.path.isfile(dest):
            if mode is not None:
                subprocess.Popen('chmod {} {}'.format(mode, dest), shell=True)
            return dest
        else:
            try:
                os.remove(dest)
            except:
                pass
            raise RuntimeError('Failed to download {} using wget'.format(URL))
    except (RuntimeError, ValueError, OSError):
        # no wget command
        env.error('Failed to download {}'.format(filename))

def calculateFileMD5(filename):
    md5 = hashlib.md5()
    # limit the calculation to the first 1G of the file content
    block_size = 2**20  # buffer of 1M
    filesize = os.path.getsize(filename)
    try:
        if filesize < 2**26:
            # for file less than 1G, use all its content
            with open(filename, 'rb') as f:
                while True:
                    data = f.read(block_size)
                    if not data:
                        break
                    md5.update(data)
        else:
            count = 64
            # otherwise, use the first and last 500M
            with open(filename, 'rb') as f:
                while True:
                    data = f.read(block_size)
                    count -= 1
                    if count == 32:
                        f.seek(-2**25, 2)
                    if not data or count == 0:
                        break
                    md5.update(data)
    except IOError as e:
        sys.exit('Failed to read {}: {}'.format(filename, e))
    return md5.hexdigest()
 
def zipdir(path, zipfile, arcroot = '/'):
    path = os.path.normpath(path)
    for root, dirs, files in os.walk(path):
        for f in files:
            zipfile.write(os.path.join(root, f), arcname = os.path.join(arcroot, root[len(path) + 1:], f))

def removeFiles(dest, exclude = [], hidden = False):
    if os.path.isdir(dest):
        for item in os.listdir(dest):
            if item.startswith('.') and hidden == False:
                continue
            if os.path.splitext(item)[1] not in exclude:
                try:
                    os.remove(os.path.join(dest,item))
                except:
                    pass

def removeEmptyDir(directory):
    try:
        if not os.listdir(directory):
            os.rmdir(directory)
    except:
        pass

def copyFiles(pattern, dist, ignore_hidden = True):
    mkpath(dist)
    for fl in glob.glob(pattern):
        if os.path.isfile(fl):
            shutil.copy(fl, dist)

def downloadResources(fromto):
    for idx, item in enumerate(fromto):
        env.log('Checking local resources {0}/{1} ...'.format(idx + 1, len(fromto)), flush = True)
        downloadURL(item[0], item[1], mode = 777)
    env.log() 
    return True

def getColumn(fn, num, delim = None, exclude = None):
    if num > 0:
        num = num - 1
    with open(fn) as inf:
        output = []
        for line in inf:
            parts = line.split(delim) if delim is not None else line.split()
            if len(parts) > num and parts[num] != exclude:
                output.append(parts[num])
    return output

def wordCount(filename):
    """Returns a word/count dict for this filename."""
    word_count = {}
    with open(filename, 'r') as input_file:
        for line in input_file:
           words = line.split()
           for word in words:
               word = word.lower()
               if not word in word_count:
                   word_count[word] = 1
               else:
                   word_count[word] += 1
    return word_count

def fileLinesCount(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

def connected_components(lists):
    neighbors = defaultdict(set)
    seen = set()
    for each in lists:
        for item in each:
            neighbors[item].update(each)
    def component(node, neighbors=neighbors, seen=seen, see=seen.add):
        nodes = set([node])
        next_node = nodes.pop
        while nodes:
            node = next_node()
            see(node)
            nodes |= neighbors[node] - seen
            yield node
    for node in neighbors:
        if node not in seen:
            yield sorted(component(node))

def listit(t):
    return list(map(listit, t)) if isinstance(t, (list, tuple)) else t

###
# Supporting functions / classes for Core.py 
###

def parseVCFline(line, exclude = []):
    if len(line) == 0:
        return None
    line = line.split('\t')
    # Skip tri-allelic variant
    if "," in line[4]:
        with env.lock:
            env.triallelic_counter.value += 1
        return None
    gs = []
    for idx in range(len(line)):
        if idx < 9 or idx in exclude:
            continue
        else:
            # Remove separater
            g = re.sub('\/|\|','',line[idx].split(":")[0])
            if g == '.' or g == '..':
                gs.append("00")
            else:
                gs.append(g.replace('1','2').replace('0','1'))
    return (line[0], line[1], line[3], line[4], line[2]), gs

def indexVCF(vcf, verbose = True):
    if not vcf.endswith(".gz"):
        if os.path.exists(vcf + ".gz"):
            if verbose:
                env.error("Cannot compress [{0}] because [{0}.gz] exists!".format(vcf), exit = True)
            else:
                sys.exit()
        if verbose:
            env.log("Compressing file [{0}] to [{0}.gz] ...".format(vcf))
        runCommand('bgzip {0}'.format(vcf))
        vcf += ".gz"
    if not os.path.isfile(vcf + '.tbi') or os.path.getmtime(vcf) > os.path.getmtime(vcf + '.tbi'):
        if verbose:
            env.log("Generating index file for [{}] ...".format(vcf))
        runCommand('tabix -p vcf -f {}'.format(vcf))
    return vcf

def extractSamplenames(vcf):
    samples = runCommand('tabix -H {}'.format(vcf))[0].strip().split('\n')[-1].split('\t')[9:]
    if not samples:
        env.error("Fail to extract samples from [{}]".format(vcf), exit = True)
    return samples

def checkVCFBundle(vcf):
    '''VCF bundle should have a .gz file and a tabix file'''
    if not vcf.endswith(".gz"):
        env.error("Input VCF file has to be bgzipped and indexed (http://samtools.sourceforge.net/tabix.shtml).",
                  exit = True)
    if not os.path.isfile(vcf + '.tbi'):
        env.error("Index file [{}] not found.".format(vcf + '.tbi'), exit = True)
    return True

def rewriteFamfile(tfam, samples, keys):
    with open(tfam, 'w') as f:
        f.write('\n'.join(['\t'.join(samples[k]) for k in keys]))
        f.write('\n')

def checkSamples(samp1, samp2):
    '''check if two sample lists agree
    1. samples in FAM but not in VCF --> ERROR
    2. samples in VCF but not in FAM --> give a message'''
    a_not_b = list(set(samp1).difference(set(samp2)))
    b_not_a = list(set(samp2).difference(set(samp1)))
    if b_not_a:
        env.log('{:,d} samples found in FAM file but not in VCF file:\n{}'.\
                           format(len(b_not_a), '\n'.join(b_not_a)))
    if a_not_b:
        env.log('{:,d} samples in VCF file will be ignored due to absence in FAM file'.format(len(a_not_b)))
    return a_not_b, b_not_a

class NoCache:
    def setID(self, ID):
        pass
    def check(self):
        return True
    def load(self, target_dir = None, names = None):
        pass
    def write(self, source_dir = None, arcroot = '/', pres = [], exts=[],
              files = [], mode = 'w'):
        pass
    def clear(self, pres = [], exts = []):
        pass

class Cache:
    def __init__(self, cache_dir, cache_name, params):
        self.cache_dir = cache_dir
        self.cache_name = os.path.join(cache_dir, cache_name + '.cache')
        self.cache_info = os.path.join(cache_dir, '.info.' + cache_name)
        self.param_info = os.path.join(cache_dir, '.conf.' + cache_name)
        mkpath(cache_dir)
        self.id = '.'
        self.params = params
        self.infofiles = [params['vcf'], params['tfam'], params['blueprint']] if params['blueprint'] else [params['vcf'], params['tfam']]
        self.infofiles.append(self.cache_name)
        self.pchecklist = {'.vcf': ['bin', 'single_markers'],
                           '.mega2':None, '.merlin':None,
                           '.linkage': ['prevalence', 'inherit_mode', 'wild_pen',
                                        'muta_pen', 'theta_max', 'theta_inc'],
                           '.analysis': ['prevalence', 'inherit_mode', 'wild_pen',
                                        'muta_pen', 'theta_max', 'theta_inc']}

    def setID(self, ID):
        self.id = "." + str(ID)

    def check(self):
        if not os.path.isfile(self.cache_info) or not os.path.isfile(self.param_info + self.id):
            return False
        with open(self.cache_info, 'r') as f:
            lines = [item.strip().split() for item in f.readlines()]
        for line in lines:
            if not os.path.isfile(line[0]) or line[1] != calculateFileMD5(line[0]):
                return False
        params = {}
        with open(self.param_info + self.id, 'r') as f:
            lines = [item.strip().split() for item in f.readlines()]
        for line in lines:
            params[line[0]] = line[1]
        if self.pchecklist[self.id]:
            for item in self.pchecklist[self.id]:
                if params[item] != str(self.params[item]):
                    return False
        return True

    def load(self, target_dir = None, names = None):
        if target_dir is None:
            target_dir = self.cache_dir
        with ZipFile(self.cache_name) as f:
            if names is None:
                mkpath(target_dir)
                f.extractall(target_dir)
            else:
                for item in f.namelist():
                    mkpath(target_dir)
                    if any([item.startswith(x) for x in names]):
                        f.extract(item, target_dir)

    def write(self, source_dir = None, arcroot = '/', pres = [], exts = [],
              files = [], mode = 'w'):
        '''Add files to cache'''
        if source_dir is None:
            source_dir = self.cache_dir
        with ZipFile(self.cache_name, mode, allowZip64 = True) as f:
            if source_dir != self.cache_dir:
                zipdir(source_dir, f, arcroot = arcroot)
            else:
                for item in os.listdir(source_dir):
                    if ((any([item.endswith(x) for x in exts]) or len(exts) == 0) \
                        and (any([item.startswith(x) for x in pres]) or len(pres) == 0)) \
                        or item in files:
                        f.write(os.path.join(source_dir, item), arcname=os.path.join(arcroot, item))
        signatures = ['{}\t{}'.format(x, calculateFileMD5(x)) for x in self.infofiles if os.path.isfile(x)]
        with open(self.cache_info, 'w') as f:
            f.write('\n'.join(signatures))
        if self.pchecklist[self.id]:
            with open(self.param_info + self.id, 'w') as f:
                f.write('\n'.join(["{}\t{}".format(item, self.params[item]) for item in self.pchecklist[self.id]]))

    def clear(self, pres = [], exts = []):
        for fl in glob.glob(self.cache_info + "*") + [self.cache_name]:
            try:
                os.remove(fl)
            except:
                pass
        #
        for pre, ext in itertools.product(pres, exts):
            for fl in glob.glob(os.path.join(self.cache_dir, pre) +  "*" + ext): 
                try:
                    os.remove(fl)
                except:
                    pass

class PseudoAutoRegion:
    def __init__(self, chrom, build):
        if build == ['hg18', 'build36'] and chrom.lower() in ['x', '23']:
            self.check = self.checkChrX_hg18
        elif build in ['hg18', 'build36'] and chrom.lower() in ['y', '24']:
            self.check = self.checkChrY_hg18
        elif build in ['hg19', 'build37'] and chrom.lower() in ['x', '23']:
            self.check = self.checkChrX_hg19
        elif build in ['hg19', 'build37'] and chrom.lower() in ['y', '24']:
            self.check = self.checkChrY_hg19
        else:
            self.check = self.notWithinRegion

    def checkChrX_hg18(self, pos):
        return (pos >= 1 and pos <= 2709520) or \
            (pos >= 154584238 and pos <= 154913754)

    def checkChrY_hg18(self, pos):
        return (pos >= 1 and pos <= 2709520) or \
            (pos >= 57443438 and pos <= 57772954)

    def checkChrX_hg19(self, pos):
        return (pos >= 60001 and pos <= 2699520) or \
            (pos >= 154931044 and pos <= 155270560)

    def checkChrY_hg19(self, pos):
        return (pos >= 10001 and pos <= 2649520) or \
            (pos >= 59034050 and pos <= 59373566)

    def notWithinRegion(self, pos):
        return False


class TFAMParser:
    def __init__(self, tfam = None):
        self.families, self.samples, self.graph = self.__parse(tfam)
        self.families_sorted = OrderedDict([(k,[]) for k in self.families])

    def is_founder(self, sid):
        return self.samples[sid][2] == "0" and self.samples[sid][3] == "0"

    def get_parents(self, sid):
        return self.samples[sid][2], self.samples[sid][3]

    def add_member(self, info):
        '''member is one line of FAM file, [fid, sid, pid, mid, sex, pheno]'''
        self.samples[info[1]] = info
        self.families_sorted[info[0]] = []
        if info[0] not in self.families:
            self.families[info[0]] = [info[1]]
        else:
            if info[1] not in self.families[info[0]]:
                self.families[info[0]].append(info[1])
        self.__update_graph(self.graph, info)

    def get_member_idx(self, sid):
        '''integer index, reflecting the order of the sample collected'''
        return self.samples.keys().index(sid)

    def get_members(self):
        return self.samples.keys()

    def print_member(self, sid):
        return ' '.join(self.samples[sid][1:])

    def sort_family(self, famid):
        '''sort samples in family such that founders precede non-founders'''
        if not self.families_sorted[famid]:
            self.families_sorted[famid] = self.__kahn_sort(famid)
        assert sorted(self.families_sorted[famid]) == sorted(self.families[famid])
        return self.families_sorted[famid]

    def __kahn_sort(self, famid):
        '''algorithm first described by Kahn (1962); implemented by Di Zhang'''
        sorted_names = []
        S_no_parents = filter(lambda x: True if self.is_founder(x) else False, self.families[famid])
        graph = self.graph[famid].copy()
        while(S_no_parents):
            n = S_no_parents.pop()
            sorted_names.append(n)
            if n not in graph:
                continue
            offsprings = graph.pop(n)
            for m in offsprings:
                father, mother = self.get_parents(m)
                if father not in graph and mother not in graph:
                    S_no_parents.append(m)
        if graph:
            raise ValueError("There is a loop in the pedigree: {}\n".format(' '.join(graph.keys())))
        else:
            return sorted_names

    def __add_or_app(self, obj, key, value):
        islist = type(value) is list
        if key not in obj:
            if not islist:
                obj[key] = [value]
            else:
                obj[key] = value
        else:
            if value not in obj[key]:
                if not islist:
                    obj[key].append(value)
                else:
                    obj[key].extend(value)

    def __update_graph(self, g, info):
        if info[2] != "0" and info[3] != "0":
            g[info[0]][info[2]].append(info[1])
            g[info[0]][info[3]].append(info[1])

    def __parse(self, tfam):
        '''Rules:
        1. samples have to have unique names
        2. both parents for a non-founder should be available
        3. founders should have at least one offspring'''
        fams = OrderedDict()
        samples = OrderedDict()
        graph = defaultdict(lambda : defaultdict(list))
        if tfam is None:
            return fams, samples, graph
        observedFounders = {}
        expectedParents = {}
        #
        # Load TFAM file
        #
        with open(tfam, 'r') as f:
            for idx, line in enumerate(f.readlines()):
                line = line.split()
                if len(line) != 6:
                    env.error("skipped line {} (has {} != 6 columns!)".format(idx, len(line)))
                    continue
                if line[1] in samples:
                    env.error("skipped line {} (duplicate sample name '{}' found!)".format(idx, line[1]))
                    continue
                # collect sample line
                samples[line[1]] = [line[0], line[1], line[2], line[3], line[4], line[5]]
                # collect family member
                self.__add_or_app(fams, line[0], line[1])
                # collect founders for family
                if line[2] in env.ped_missing and line[3] in env.ped_missing:
                    self.__add_or_app(observedFounders, line[0], line[1])
                else:
                    self.__add_or_app(expectedParents, line[0], (line[1], line[2], line[3]))
        #
        # Check sample parents
        #
        for k in expectedParents:
            for person in expectedParents[k]:
                if not (person[1] in fams[k] and person[2] in fams[k]):
                    env.error("Cannot find parents ({} and {}) of {} in [{}]!".\
                              format(person[1], person[2], person[0], tfam), exit = True)
                    # missing both parents, make it a founder
                    # samples[person[0]][2] = samples[person[0]][3] = "0"
                    # observedFounders[k].append(person[0])
                if person[1] in fams[k] and not person[2] in fams[k]:
                    env.error("Cannot find mother ({}) of {} in [{}]!".\
                              format(person[2], person[0], tfam), exit = True)
                    # missing mother, mask as zero
                    # samples[person[0]][3] = "0"
                if not person[1] in fams[k] and person[2] in fams[k]:
                    env.error("Cannot find father ({}) of {} in [{}]!".\
                              format(person[1], person[0], tfam), exit = True)
                    # missing father, mask as zero
                    # samples[person[0]][2] = "0"
        #
        # Remove trivial families
        #
        for k in fams.keys():
            if Counter(observedFounders[k]) == Counter(fams[k]):
                del fams[k]
                continue
        #
        valid_samples = []
        for value in fams.values():
            valid_samples.extend(value)
        samples = {k : samples[k] for k in valid_samples}
        #
        for item in samples.values():
            self.__update_graph(graph, item)
        return fams, samples, graph
