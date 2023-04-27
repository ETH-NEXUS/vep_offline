#!/usr/bin/env python3

from pathlib import Path
from os import environ, remove
from os.path import join, splitext, sep
from sys import argv, stdout
from glob import glob
import re
from friendlylog import colored_logger as log
import tarfile
import gzip
from subprocess import Popen, PIPE, STDOUT
from shutil import move, copyfileobj
import sh

DATA = '/opt/vep/.vep'
INSTALLED = Path(join(sep, '.installed'))

CACHE = {
    'GRCh37': 'http://ftp.ensembl.org/pub/release-{}/variation/indexed_vep_cache/homo_sapiens_merged_vep_{}_GRCh37.tar.gz',
    'GRCh38': 'http://ftp.ensembl.org/pub/release-{}/variation/indexed_vep_cache/homo_sapiens_merged_vep_{}_GRCh38.tar.gz',
}

LATEST_CACHE = {
    'GRCh37': 'http://ftp.ensembl.org/pub/current-variation/indexed_vep_cache/homo_sapiens_merged_vep_*_GRCh37.tar.gz',
    'GRCh38': 'http://ftp.ensembl.org/pub/current-variation/indexed_vep_cache/homo_sapiens_merged_vep_*_GRCh38.tar.gz',
}

# The last GRCh37 fasta file is in release 75:
FASTA = {
    'GRCh37': 'http://ftp.ensembl.org/pub/release-75/fasta/homo_sapiens/dna/Homo_sapiens.GRCh37.75.dna.primary_assembly.fa.gz',
    'GRCh38': 'http://ftp.ensembl.org/pub/release-{}/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz'
}

LATEST_FASTA = {
    'GRCh37': 'http://ftp.ensembl.org/pub/release-75/fasta/homo_sapiens/dna/Homo_sapiens.GRCh37.75.dna.primary_assembly.fa.gz',
    'GRCh38': 'http://ftp.ensembl.org/pub/current-fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz'
}

INDICATORS = ['\\', '|', '/', '|']
indicator_idx = 0

rsync = sh.Command('rsync')
tar = sh.Command('tar')
gunzip = sh.Command('gunzip')


def next_indicator():
    global indicator_idx
    indicator_idx = (indicator_idx + 1) % len(INDICATORS)
    return INDICATORS[indicator_idx]


def __rsync_and_extract(url, force=False):
    # replace http with rsync
    url = re.sub(r'http(s)?://', r'rsync://', url)
    # change the location of the file
    url = re.sub(r'rsync://ftp.ensembl.org/', r'rsync://ftp.ensembl.org/ensembl/', url)
    local_file = join(DATA, re.sub(r'.*/', '', url))
    if force or not Path(local_file).is_file():
        log.info(f">>> Downloading {url}...")
        params = ['-avh', '--info=progress2', '--stats', '--human-readable', url, DATA]
        proc = rsync(*params, _err_to_out=True, _iter=True)
        for line in proc:
            stdout.write(line)
            stdout.flush()
        log.info(f">>> Downloaded {local_file} with exit code {proc.exit_code}.")
        if proc.exit_code == 0:
            log.info(f">>> Extracting {local_file}...")
            if local_file.endswith('.tar.gz'):
                params = ['-xzf', local_file, '-C', DATA]
                proc = tar(*params, _err_to_out=True, _iter=True)
                for line in proc:
                    stdout.write(line)
                    stdout.flush()
                log.info(f">>> Extracted {local_file}.")
            elif local_file.endswith('.gz'):
                if not Path(splitext(local_file)[0]).exists():
                    proc = gunzip(local_file, _err_to_out=True, _iter=True)
                    for line in proc:
                        stdout.write(line)
                        stdout.flush()
                log.info(f">>> Extracted {local_file}.")
            else:
                log.error(f"Cannot extract {local_file}.")
        else:
            raise Exception(
                f"Error rsyncing file '{url}'': {rsync.returncode}")
    else:
        log.warning(
            f"File {local_file} already exists, skipping.")


# def __unzip(file, dir):
#     try:
#         if splitext(file)[1] == '.gz':
#             new_file = join(dir, re.sub(r'.*/', '', splitext(file)[0]))
#             if not Path(new_file).is_file():
#                 log.info(f"Gunzip {file} to {new_file}...")
#                 with gzip.open(file, 'rb') as gz, open(new_file, 'wb') as decompressed:
#                     copyfileobj(gz, decompressed)
#                 file = new_file
#         if splitext(file)[1] == '.tar':
#             log.info(f"Untar {file} to {dir}...")
#             with tarfile.open(file) as tar:
#                 tar.extractall(dir)
#     except Exception as ex:
#         raise Exception(f"Cannot unzip file {file}: {ex}")


def __cleanup():
    log.info(f"Removing temporary files from the cache ({DATA})...")
    files = glob(join(DATA, 'tmp*'))
    for file in files:
        try:
            remove(file)
        except Exception as ex:
            log.error(ex)


def populate_cache(release, noGRCh37=False, force=False):
    __cleanup()
    if not INSTALLED.is_file() or force:
        log.info('Populating VEP cache...')
        log.warning('...this can take a VERY LONG time...')
        log.warning('...please be patient.')
        try:
            if release == 'latest':
                __rsync_and_extract(LATEST_FASTA['GRCh38'], force=True)
                __rsync_and_extract(LATEST_CACHE['GRCh38'], force=True)
                noGRCh37 or __rsync_and_extract(LATEST_FASTA['GRCh37'], force=True)
                noGRCh37 or __rsync_and_extract(LATEST_CACHE['GRCh37'], force=True)
            else:
                __rsync_and_extract(FASTA['GRCh38'].format(release), force=True)
                __rsync_and_extract(CACHE['GRCh38'].format(release, release), force=True)
                noGRCh37 or __rsync_and_extract(FASTA['GRCh37'], force=True)
                noGRCh37 or __rsync_and_extract(CACHE['GRCh37'].format(release, release), force=True)

            INSTALLED.touch()
        except Exception as ex:
            raise Exception(f"Error populating cache: {ex}")
    else:
        log.info('VEP cache is already populated, doing nothing.')


if __name__ == '__main__':
    vep_version = environ.get('VEP_VERSION').split('.')[0]
    if vep_version:
        force = False
        if len(argv) > 1 and argv[1] == '-f':
            force = True
        noGRCh37 = environ.get('DISABLE_GRCH37', 'false').lower() == 'true'
        populate_cache(vep_version, noGRCh37, force)
    else:
        log.error("Environment variable VEP_VERSION is not set!")
