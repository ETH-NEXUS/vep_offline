#!/usr/bin/env python3

from pathlib import Path
from os import environ, remove
from os.path import join, splitext, sep
from sys import argv
from glob import glob
import re
from friendlylog import colored_logger as log
import tarfile
import gzip
from subprocess import Popen, PIPE, STDOUT
from shutil import move

DATA = '/opt/vep/.vep'
INSTALLED = Path(join(sep, '.installed'))

CACHE = {
    'GRCh37': 'http://ftp.ensembl.org/pub/release-{}/variation/indexed_vep_cache/homo_sapiens_merged_vep_{}_GRCh37.tar.gz',
    'GRCh38': 'http://ftp.ensembl.org/pub/release-{}/variation/indexed_vep_cache/homo_sapiens_merged_vep_{}_GRCh38.tar.gz',
}

# The last GRCh37 fasta file is in release 75:
FASTA = {
    'GRCh37': 'http://ftp.ensembl.org/pub/release-75/fasta/homo_sapiens/dna/Homo_sapiens.GRCh37.75.dna.primary_assembly.fa.gz',
    'GRCh38': 'http://ftp.ensembl.org/pub/release-{}/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz'
}

INDICATORS = ['\\', '|', '/', '|']
indicator_idx = 0


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
        command = ['rsync', '-ahP', url, DATA]
        log.info(f"Executing '{' '.join(command)}'...")
        with Popen(command, shell=False, stdout=PIPE, stderr=STDOUT, bufsize=1, universal_newlines=True) as rsync:
            nl = r'\n'
            for line in rsync.stdout:
                print(
                    f"{re.sub(r'.*/', '', url)}: {re.sub(nl, '', line)}", end='\r')
        if rsync.returncode == 0:
            __unzip(local_file, DATA)
        else:
            raise Exception(
                f"Error rsyncing file '{url}'': {rsync.returncode}")
    else:
        log.warning(
            f"File {local_file} already exists, skipping.")


def __unzip(file, dir):
    try:
        if splitext(file)[1] == '.gz':
            log.info(f"Gunzip {file}...")
            with gzip.open(file, 'r') as gz:
                file_content = gz.read()
                file = splitext(file)[0]
                new_file = join(dir, re.sub(r'.*/', '', file))
                if not Path(new_file).is_file():
                    with open(file, 'wb') as decompressed:
                        decompressed.write(file_content)
                    move(file, new_file)
                file = new_file
        if splitext(file)[1] == '.tar':
            log.info(f"Untar {file} to {dir}...")
            with tarfile.open(file) as tar:
                tar.extractall(dir)
    except Exception as ex:
        raise Exception(f"Cannot unzip file {file}: {ex}")


def __cleanup():
    log.info(f"Removing temporary files from the cache ({DATA})...")
    files = glob(join(DATA, 'tmp*'))
    for file in files:
        try:
            remove(file)
        except Exception as ex:
            log.error(ex)


def populate_cache(release, force=False):
    __cleanup()
    if not INSTALLED.is_file() or force:
        log.info('Populating VEP cache...')
        log.warning('...this can take a VERY LONG time...')
        log.warning('...please be patient.')
        try:
            __rsync_and_extract(
                CACHE['GRCh37'].format(release, release), force=True)
            __rsync_and_extract(
                CACHE['GRCh38'].format(release, release), force=True)
            __rsync_and_extract(
                FASTA['GRCh37'], force=True)
            __rsync_and_extract(
                FASTA['GRCh38'].format(release), force=True)
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
        populate_cache(vep_version, force)
    else:
        log.error("Environment variable VEP_VERSION is not set!")
