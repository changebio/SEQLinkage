# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/04_Main.ipynb (unless otherwise specified).

__all__ = ['Args', 'HOMEPAGE', 'checkParams', 'main']

# Cell
from argparse import ArgumentParser, ArgumentTypeError, RawDescriptionHelpFormatter, SUPPRESS
import os, glob, platform
from multiprocessing import cpu_count, Queue
from .Utils import *
from .Runner import *
from .Core import *
from multiprocessing import Process, Queue
from collections import OrderedDict
import itertools
from copy import deepcopy
import sys, faulthandler, platform
import numpy as np
import os
if sys.version_info.major == 2:
    from cstatgen import cstatgen_py2 as cstatgen
    from cstatgen.egglib import Align
else:
    from cstatgen import cstatgen_py3 as cstatgen
    import egglib
    from egglib import Align
HOMEPAGE = 'http://bioinformatics.org/seqlink'  #fixme
class Args:
    def __init__(self):
        self.parser = ArgumentParser(
        description = '''\t{}, linkage analysis using sequence data\n\t[{}]'''.\
        format(env.proj, env.version),
        formatter_class = RawDescriptionHelpFormatter,
        prog = env.prog,
        fromfile_prefix_chars = '@', add_help = False,
        epilog = '''\tCopyright (c) 2013 - 2014 Gao Wang <wang.gao@columbia.edu>\n\tDistributed under GNU General Public License\n\tHome page: {}'''.format(HOMEPAGE))
        self.getEncoderArguments(self.parser)
        self.getIOArguments(self.parser)
        self.getLinkageArguments(self.parser)
        self.getRuntimeArguments(self.parser)
        self.parser.set_defaults(func=main)

    def isalnum(self, string):
        if not os.path.basename(string).isalnum():
            raise ArgumentTypeError("Illegal path name [%]: must be alphanumerical string." % string)
        return string

    def get(self):
        return self.parser.parse_args()

    def getEncoderArguments(self, parser):
        vargs = parser.add_argument_group('Collapsed haplotype pattern method arguments')
        vargs.add_argument('--bin', metavar = "FLOAT", default = 0, type = float,
                           help='''Defines theme to collapse variants. Set to 0 for "complete collapsing",
        1 for "no collapsing", r2 value between 0 and 1 for "LD based collapsing" and other integer values for customized
        collapsing bin sizes. Default to 0 (all variants will be collapsed).''')
        vargs.add_argument('-b', '--blueprint', metavar = 'FILE',
                           help='''Blueprint file that defines regional marker
        (format: "chr startpos endpos name avg.distance male.distance female.distance").''')
        vargs.add_argument('--single-markers', action='store_true', dest = "single_markers",
                           help='''Use single variant markers. This switch will overwrite
        "--bin" and "--blueprint" arguments.''')

    def getIOArguments(self, parser):
        vargs = parser.add_argument_group('Input / output options')
        vargs.add_argument('--fam', metavar='FILE', required=True, dest = "tfam",
                           help='''Input pedigree and phenotype information in FAM format.''')
        vargs.add_argument('--vcf', metavar='FILE', required=True, help='''Input VCF file, bgzipped.''')
        vargs.add_argument('--anno', metavar='FILE', required=False, help='''Input annotation file from annovar.''')
        vargs.add_argument('--pop', metavar='FILE', required=False, help='''Input two columns file, first column is family ID,second column population information.''')
        vargs.add_argument('--build', metavar='STRING', default='hg19', choices = ["hg19", "hg38"], help='''Reference genome version for VCF file.''')
        vargs.add_argument('--prephased', action='store_true', help=SUPPRESS)
        vargs.add_argument('--freq', metavar='INFO', default = None,help='''Info field name for allele frequency in VCF file.''')
        vargs.add_argument('--freq_by_fam', metavar='INFO', help='''Per family info field name for allele frequency in VCF file.''')
        vargs.add_argument('--mle', action='store_true', help='''Estimate allele frequency using MERLIN's MLE method.''')
        vargs.add_argument('--rvhaplo', action='store_true', help='''Only using rare variants for haplotyping''')
        vargs.add_argument('--recomb_max', metavar='INT', default = 1, type = int, help='''Maximum recombination events allowed per region.''')
        vargs.add_argument('--recomb_cross_fam', action='store_true', help='''Code sub-regions with cross family recombination events; otherwise sub-regions are generated on per family basis.''')
        vargs.add_argument('--rsq', metavar='R', default=0.0,type=float, help=SUPPRESS)
        vargs.add_argument('--include_vars', metavar='FILE', help='''Variants to be included in CHP construction''')
        vargs.add_argument('-c', '--maf-cutoff', metavar='P', default=1.0, type=float, dest = "maf_cutoff",
                           help='''MAF cutoff to define "common" variants to be excluded from analyses.''')
        vargs.add_argument('--chrom-prefix', metavar='STRING', dest = 'chr_prefix',
                           help='''Prefix to chromosome name in VCF file if applicable, e.g. "chr".''')
        vargs.add_argument('-o', '--output', metavar='Name', type = self.isalnum,
                           help='''Output name prefix.''')
        vargs.add_argument('-f', '--format', metavar = 'FORMAT', nargs='+',
                           choices = ["LINKAGE", "MERLIN", "MEGA2", "PLINK"], default=['LINKAGE'],
                           help='''Output format. Default to LINKAGE.''')

    def getRuntimeArguments(self, parser):
        vargs = parser.add_argument_group('Runtime arguments')
        vargs.add_argument("-h", "--help", action="help", help="Show help message and exit.")
        vargs.add_argument('-j', '--jobs', metavar='N', type = int, default = max(min(int(cpu_count() / 2), 32), 1),
                           help='''Number of CPUs to use.''')
        vargs.add_argument('--tempdir', metavar='PATH',
                           help='''Temporary directory to use.''')
        vargs.add_argument('--cache', action='store_false', dest = 'vanilla',
                           help='''Load cache data for analysis instead of starting from scratch.''')
        vargs.add_argument('-q', '--quiet', action='store_true', help='Disable the display of runtime MESSAGE.')
        vargs.add_argument('--debug', action='store_true', help=SUPPRESS)
        vargs.add_argument('--no-save', action='store_true', dest='no_save', help=SUPPRESS)

    def getLinkageArguments(self, parser):
        vargs = parser.add_argument_group('LINKAGE options')
        vargs.add_argument('-K', '--prevalence', metavar='FLOAT', type=float,
                           help='Disease prevalence.')
        vargs.add_argument('--moi', metavar='STRING', dest = "inherit_mode",
                           # choices=['AD', 'AR', 'Xlinked', 'Y'],
                           choices=['AD', 'AR'],
                           help='Mode of inheritance, AD/AR: autosomal dominant/recessive.')
        vargs.add_argument('-W', '--wt-pen', metavar='FLOAT', type=float, dest = "wild_pen",
                           help='Penetrance for wild type.')
        vargs.add_argument('-M', '--mut-pen', metavar='FLOAT', type=float, dest = "muta_pen",
                           help='Penetrance for mutation.')
        vargs.add_argument('--theta-max', metavar='FLOAT', type=float, dest = "theta_max", default = 0.5,
                           help='Theta upper bound. Default to 0.5.')
        vargs.add_argument('--theta-inc', metavar='FLOAT', type=float, dest = "theta_inc", default = 0.05,
                           help='Theta increment. Default to 0.05.')
        if ((platform.system() == 'Linux' or platform.system() == 'Darwin') and platform.architecture()[0] == '64bit'):
            vargs.add_argument('--run-linkage', action='store_true', dest = "run_linkage",
                           help='''Perform Linkage analysis using FASTLINK program.''')
            vargs.add_argument('--output-entries', metavar='N', type=int, dest = "output_limit", default = 10,
                           help='Write the highest N LOD/HLOD scores to output tables. Default to 10.')

# Cell
def checkParams(args):
    '''set default arguments or make warnings'''
    env.debug = args.debug
    env.quiet = args.quiet
    env.prephased = args.prephased
    args.vcf = os.path.abspath(os.path.expanduser(args.vcf))
    args.tfam = os.path.abspath(os.path.expanduser(args.tfam))
    for item in [args.vcf, args.tfam]:
        if not os.path.exists(item):
            env.error("Cannot find file [{}]!".format(item), exit = True)
    if args.output:
        env.outdir = args.output
        env.cache_dir = os.path.join(os.path.dirname(args.output), 'cache')
        env.tmp_log = os.path.join(env.tmp_dir, env.output + ".STDOUT")
    #
    if len([x for x in set(getColumn(args.tfam, 6)) if x.lower() not in env.ped_missing]) > 2:
        env.trait = 'quantitative'
    env.log('{} trait detected in [{}]'.format(env.trait.capitalize(), args.tfam))
    if not args.blueprint:
        args.blueprint = os.path.join(env.resource_dir, 'genemap.{}.txt'.format(args.build))
    args.format = [x.lower() for x in set(args.format)]
    if args.run_linkage and "linkage" not in args.format:
        args.format.append('linkage')
    if None in [args.inherit_mode, args.prevalence, args.wild_pen, args.muta_pen] and "linkage" in args.format:
        env.error('To generate LINKAGE format or run LINKAGE analysis, please specify all options below:\n\t--prevalence, -K\n\t--moi\n\t--wild-pen, -W\n\t--muta-pen, -M', show_help = True, exit = True)
    if args.tempdir is not None:
        env.ResetTempdir(args.tempdir)
    return True

# Cell
def main(args):
    '''the main encoder function'''
    checkParams(args)
    download_dir = 'http://bioinformatics.org/spower/download/.private'
    downloadResources([('{}/genemap.{}.txt'.format(download_dir, args.build), env.resource_dir),
                       ('{}/{}/mlink'.format(download_dir, platform.system().lower()), env.resource_bin),
                       ('{}/{}/unknown'.format(download_dir, platform.system().lower()), env.resource_bin),
                       ('{}/{}/makeped'.format(download_dir, platform.system().lower()), env.resource_bin),
                       ('{}/{}/pedcheck'.format(download_dir, platform.system().lower()), env.resource_bin)])
    if args.no_save:
        cache = NoCache()
    else:
        cache = Cache(env.cache_dir, env.output, vars(args))
    cache.setID('vcf')
    # STEP 1: write encoded data to TPED format
    if not args.vanilla and cache.check():
        env.log('Loading regional marker data from archive ...')
        cache.load(target_dir = env.tmp_dir, names = ['CACHE'])
        env.success_counter.value = sum(map(fileLinesCount, glob.glob('{}/*.tped'.format(env.tmp_cache))))
        env.batch = 10
    else:
        # load data
        data = RData(args.vcf, args.tfam,args.anno,args.pop,allele_freq_info=args.freq)
        samples_vcf = data.samples_vcf

        if len(samples_vcf) == 0:
            env.error("Fail to extract samples from [{}]".format(args.vcf), exit = True)
        env.log('{:,d} samples found in [{}]'.format(len(samples_vcf), args.vcf))
        samples_not_vcf = data.samples_not_vcf

        if len(data.families) == 0:
            env.error('No valid family to process. ' \
                      'Families have to be at least trio with at least one member in VCF file.', exit = True)
        if len(data.samples) == 0:
            env.error('No valid sample to process. ' \
                      'Samples have to be in families, and present in both TFAM and VCF files.', exit = True)
        rewriteFamfile(os.path.join(env.tmp_cache, '{}.tfam'.format(env.output)),
                       data.tfam.samples, list(data.samples.keys()) + samples_not_vcf)
        if args.single_markers:
            regions = [(x[0], x[1], x[1], "{}:{}".format(x[0], x[1]), '.', '.', '.')
                       for x in data.vs.GetGenomeCoordinates()]
            args.blueprint = None
        else:
            # load blueprint
            try:
                env.log('Loading marker map from [{}] ...'.format(args.blueprint))
                with open(args.blueprint, 'r') as f:
                    regions = [x.strip().split() for x in f.readlines()]
            except IOError:
                env.error("Cannot load regional marker blueprint [{}]. ".format(args.blueprint), exit = True)
        env.log('{:,d} families with a total of {:,d} samples will be scanned for {:,d} pre-defined units'.\
                format(len(data.families), len(data.samples), len(regions)))
        env.jobs = max(min(args.jobs, len(regions)), 1)
        env.log('Phasing haplotypes log file: [{}]'.format(env.tmp_log + str(os.getpid()) + '.log'))
        regions.extend([None] * env.jobs)
        queue = Queue()
        try:
            faulthandler.enable(file=open(env.tmp_log + '.SEGV', 'w'))
            for i in regions:
                queue.put(i)
            jobs = [EncoderWorker(
                queue, len(regions), data,
                RegionExtractor(args.vcf, chr_prefix = args.chr_prefix),
                MarkerMaker(args.bin, maf_cutoff = args.maf_cutoff),
                LinkageWriter(len(samples_not_vcf))
                ) for i in range(env.jobs)]
            for j in jobs:
                j.start()
            for j in jobs:
                j.join()
            faulthandler.disable()
        except KeyboardInterrupt:
            # FIXME: need to properly close all jobs
            raise ValueError("Use 'killall {}' to properly terminate all processes!".format(env.prog))
        else:
            env.log('{:,d} units (from {:,d} variants) processed; '\
                '{:,d} Mendelian inconsistencies and {:,d} recombination events handled\n'.\
                format(env.success_counter.value,
                       env.variants_counter.value,
                       env.mendelerror_counter.value,
                       env.recomb_counter.value), flush = True)
            if env.triallelic_counter.value:
                env.log('{:,d} tri-allelic loci were ignored'.format(env.triallelic_counter.value))
            if env.commonvar_counter.value:
                env.log('{:,d} variants ignored due to having MAF > {}'.\
                        format(env.commonvar_counter.value, args.maf_cutoff))
            if env.null_counter.value:
                env.log('{:,d} units ignored due to absence in VCF file'.format(env.null_counter.value))
            if env.trivial_counter.value:
                env.log('{:,d} units ignored due to absence of variation in samples'.format(env.trivial_counter.value))
            fatal_errors = 0
            try:
                # Error msg from C++ extension
                os.system("cat {}/*.* > {}".format(env.tmp_dir, env.tmp_log))
                fatal_errors = wordCount(env.tmp_log)['fatal']
            except KeyError:
                pass
            if env.chperror_counter.value:
                env.error("{:,d} regional markers failed to be generated due to haplotyping failures!".\
                          format(env.chperror_counter.value))
            if fatal_errors:
                env.error("{:,d} or more regional markers failed to be generated due to runtime errors!".\
                          format(fatal_errors))
            env.log('Archiving regional marker data to directory [{}]'.format(env.cache_dir))
            cache.write(arcroot = 'CACHE', source_dir = env.tmp_cache)
    env.jobs = args.jobs
    # STEP 2: write to PLINK or mega2 format
    tpeds = [os.path.join(env.tmp_cache, item) for item in os.listdir(env.tmp_cache) if item.startswith(env.output) and item.endswith('.tped')]
    print(tpeds) #testing line
    for fmt in args.format:
        print(fmt.lower())
        cache.setID(fmt.lower())
        if not args.vanilla and cache.check():
            env.log('Loading {} data from archive ...'.format(fmt.upper()))
            cache.load(target_dir = env.tmp_dir, names = [fmt.upper()])
        else:
            env.log('{:,d} units will be converted to {} format'.format(env.success_counter.value, fmt.upper()))
            env.format_counter.value = 0
            format(tpeds, os.path.join(env.tmp_cache, "{}.tfam".format(env.output)),
                   args.prevalence, args.wild_pen, args.muta_pen, fmt,
                   args.inherit_mode, args.theta_max, args.theta_inc)
            env.log('{:,d} units successfully converted to {} format\n'.format(env.format_counter.value, fmt.upper()), flush = True)
            if env.skipped_counter.value:
                # FIXME: perhaps we need to rephrase this message?
                env.log('{} region - family pairs skipped'.format(env.skipped_counter.value))
            env.log('Archiving {} format to directory [{}]'.format(fmt.upper(), env.cache_dir))
            cache.write(arcroot = fmt.upper(),
                        source_dir = os.path.join(env.tmp_dir, fmt.upper()), mode = 'a')
    mkpath(env.outdir)
    if args.run_linkage:
        cache.setID('analysis')
        if not args.vanilla and cache.check():
            env.log('Loading linkage analysis result from archive ...'.format(fmt.upper()))
            cache.load(target_dir = env.outdir, names = ['heatmap'])
        else:
            env.log('Running linkage analysis ...'.format(fmt.upper()))
            run_linkage(args.blueprint, args.theta_inc, args.theta_max, args.output_limit)
            env.log('Linkage analysis succesfully performed for {:,d} units\n'.\
                    format(env.run_counter.value, fmt.upper()), flush = True)
            if env.makeped_counter.value:
                env.log('{} "makeped" runtime errors occurred'.format(env.makeped_counter.value))
            if env.pedcheck_counter.value:
                env.log('{} "pedcheck" runtime errors occurred'.format(env.pedcheck_counter.value))
            if env.unknown_counter.value:
                env.log('{} "unknown" runtime errors occurred'.format(env.unknown_counter.value))
            if env.mlink_counter.value:
                env.log('{} "mlink" runtime errors occurred'.format(env.mlink_counter.value))
            cache.write(arcroot = 'heatmap', source_dir = os.path.join(env.outdir, 'heatmap'), mode = 'a')
        html(args.theta_inc, args.theta_max, args.output_limit)
    else:
        env.log('Saving data to [{}]'.format(os.path.abspath(env.outdir)))
        cache.load(target_dir = env.outdir)