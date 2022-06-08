#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from urllib import parse
import tempfile
import re
import json
from os.path import join
import subprocess

DATA = '/opt/vep/.vep'


class Handler(BaseHTTPRequestHandler):
    def __run_vep(self, input: list, **vep_options):
        (_, input_file) = tempfile.mkstemp(suffix='.vcf', dir='/tmp')
        with open(input_file, 'w') as inf:
            sep = '\t'
            for line in input:
                # print('--line--', f"{re.sub(r'[ ]+', tab, line)}\n")
                inf.write(f"{re.sub(r'[ ]+', sep, line)}\n")
        (_, output_file) = tempfile.mkstemp(suffix='.json', dir='/tmp')

        fasta = 'Homo_sapiens.GRCh38.dna.primary_assembly.fa' if vep_options.get(
            'assembly') == 'GRCh38' else 'Homo_sapiens.GRCh37.75.dna.primary_assembly.fa'

        vep_args = {
            'cache': True,
            'offline': True,
            'merged': True,
            'use_given_ref': True,
            'assembly': 'GRCh38',
            'fasta': join(DATA, fasta),
            'canonical': True,
            'hgvs': True,
            'hgvsg': True,
            'symbol': True,
            'xref_refseq': True,
            'af_gnomad': True,
            'input_file': input_file,
            # This is autodetected: 'format': 'vcf' if vcf_format else 'ensembl',
            'output_file': output_file,
            'json': True,
            'force_overwrite': True,
            'dir_cache': DATA,
            'dir_plugins': join(DATA, 'Plugins'),
            'sift': 'b',
            'uniprot': True,
            'ccds': True,
            'max_af': True,
            'variant_class': True,
            'gene_phenotype': True,
            'numbers': True,
            'show_ref_allele': True,
            'shift_genomic': '1',
            'shift_3prime': '1',
            'shift_length': True,
            'protein': True,
            'tsl': True,
            'appris': True,
            'biotype': True,
            'domains': True,
            'af': True,
            'max_af': True,
            'af_1kg': True,
            'af_esp': True,
            'af_gnomad': True,
            # 'af_exac': True,
            'pubmed': True,
            'var_synonyms': True,
            'flag_pick': True,
            'sift': 'b',
            'polyphen': 'b',
            'ccds': True,
            'hgvs': True,
            'symbol': True,
            'numbers': True,
            'domains': True,
            'regulatory': True,
            'canonical': True,
            'protein': True,
            'biotype': True,
            'af': True,
            'af_1kg': True,
            'af_esp': True,
            'af_gnomad': True,
            'max_af': True,
            'pubmed': True,
            'uniprot': True,
            'mane': True,
            # 'mane_select': True,
            'tsl': True,
            'appris': True,
            'variant_class': True,
            'gene_phenotype': True,
            'mirna': True,
            'plugins': 'AncestralAllele,Blosum62,CADD,CSN,Carol,Condel,Conservation,DisGeNET,Downstream,Draw,ExAC,ExACpLI,FATHMM,FATHMM_MKL,FlagLRG,FunMotifs,G2P,GO,GeneSplicer,Gwava,HGVSIntronOffset,LD,LOVD,LoF,LoFtool,LocalID,MPC,MTR,Mastermind,MaxEntScan,NearestExonJB,NearestGene,PON_P2,Phenotypes,PostGAP,ProteinSeqs,REVEL,ReferenceQuality,SameCodon,SingleLetterAA,SpliceAI,SpliceRegion,StructuralVariantOverlap,SubsetVCF,TSSDistance,dbNSFP,dbscSNV,gnomADc,miRNA,neXtProt,satMutMPRA'
        }
        vep_args.update(vep_options)
        command = ['/opt/vep/src/ensembl-vep/vep']
        for key, value in vep_args.items():
            if value:
                command.append(f"--{key}")
            if value != True:
                command.append(str(value))

        # print('command', ' '.join(command))

        result = subprocess.run(command, stdout=subprocess.PIPE)
        result.stdout

        with open(output_file, 'r') as outf:
            ret = []
            for line in outf.readlines():
                # print(line)
                ret.append(json.loads(line))
        return ret

    def __output_error(self, msg):
        self.send_response(404)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(
            {'error': f"{msg}"}).encode('utf-8'))

    def do_GET(self):
        query_params = parse.parse_qs(parse.urlsplit(self.path).query)
        print('query_params', query_params)
        query = query_params.get('q', None)
        if not query:
            self.__output_error('param q must be given')
            return
        vep_input = []
        for q in query:
            parts = q.split('_')
            if len(parts) == 4:
                vep_input.append("{} {} . {} {}".format(*parts))
            elif len(parts) == 5:
                vep_input.append("{} {} {} {} {}".format(*parts))
            else:
                self.__output_error(
                    'wrong format in q parameter should be chr_position_ref_alt of chr_start_end_ref_alt')
                return
        # print('vep_input', vep_input)
        vep_options = query_params.copy()
        vep_options = {k: False if v[0] in ['0', 'false'] else True if v[0] in [
            '1', 'true'] else v[0] for k, v in vep_options.items()}
        del vep_options['q']
        print('vep_options', vep_options)
        vep_data = self.__run_vep(vep_input, **vep_options)
        # print('vep_data', vep_data)
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(vep_data).encode('utf-8'))
        return


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


if __name__ == '__main__':
    webServer = ThreadedHTTPServer(('0.0.0.0', 5005), Handler)
    print("Server started.")

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
