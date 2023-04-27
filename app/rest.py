#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from urllib import parse
import tempfile
import re
import json
from os.path import join
import subprocess

DATA = "/opt/vep/.vep"


class Handler(BaseHTTPRequestHandler):
    def __run_vep(self, input: list, **vep_options):
        (_, input_file) = tempfile.mkstemp(suffix=".vcf", dir="/tmp")
        with open(input_file, "w") as inf:
            sep = "\t"
            for line in input:
                # print('--line--', f"{re.sub(r'[ ]+', tab, line)}\n")
                inf.write(f"{re.sub(r'[ ]+', sep, line)}\n")
        (_, output_file) = tempfile.mkstemp(suffix=".json", dir="/tmp")

        fasta = (
            "Homo_sapiens.GRCh38.dna.primary_assembly.fa"
            if vep_options.get("assembly") == "GRCh38"
            else "Homo_sapiens.GRCh37.75.dna.primary_assembly.fa"
        )

        # Arguments for the control flow
        vep_args = {
            "dir_cache": DATA,
            "dir_plugins": join(DATA, "Plugins"),
            "fasta": join(DATA, fasta),
            # This is autodetected: 'format': 'vcf' if vcf_format else 'ensembl',
            "input_file": input_file,
            "output_file": output_file,
        }
        # Editable arguments with default values (copy this to the README)
        vep_args.update(
            {
                "af": True,
                "af_1kg": True,
                "af_gnomad": True,
                "appris": True,
                "assembly": "GRCh38",
                "biotype": True,
                "cache": True,
                "canonical": True,
                "ccds": True,
                "domains": True,
                "flag_pick": True,
                "force_overwrite": True,
                "gene_phenotype": True,
                "hgvs": True,
                "hgvsg": True,
                "json": True,
                "mane": True,
                "max_af": True,
                "merged": True,
                "mirna": True,
                "numbers": True,
                "offline": True,
                "polyphen": "b",
                "protein": True,
                "pubmed": True,
                "regulatory": True,
                "shift_3prime": 1,
                "shift_genomic": True,
                "shift_length": True,
                "show_ref_allele": True,
                "sift": "b",
                "symbol": True,
                "tsl": True,
                "uniprot": True,
                "use_given_ref": True,
                "var_synonyms": True,
                "variant_class": True,
                "xref_refseq": True,
            }
        )

        # TODO: Plugins
        # vep_args.update({
        # 'plugin': 'CADD,CSN,Carol,Condel,Conservation,DisGeNET,Downstream,Draw,ExAC,ExACpLI,FATHMM,FATHMM_MKL,FlagLRG,FunMotifs,G2P,GO,GeneSplicer,Gwava,HGVSIntronOffset,LD,LOVD,LoF,LoFtool,LocalID,MPC,MTR,Mastermind,MaxEntScan,NearestExonJB,NearestGene,PON_P2,Phenotypes,PostGAP,ProteinSeqs,REVEL,ReferenceQuality,SameCodon,SingleLetterAA,SpliceAI,SpliceRegion,StructuralVariantOverlap,SubsetVCF,TSSDistance,dbNSFP,dbscSNV,gnomADc,miRNA,neXtProt,satMutMPRA'
        # 'plugin': 'Draw,images/,1000,100'
        # })

        vep_args.update(vep_options)
        command = ["/opt/vep/src/ensembl-vep/vep"]
        for key, value in vep_args.items():
            if value:
                command.append(f"--{key}")
            if value is not True:
                command.append(str(value))

        print("command", " ".join(command))

        result = subprocess.run(command, stdout=subprocess.PIPE)
        result.stdout

        with open(output_file, "r") as outf:
            ret = []
            for line in outf.readlines():
                # print(line)
                ret.append(json.loads(line))
        return ret

    def __output_error(self, msg):
        self.send_response(404)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": f"{msg}"}).encode("utf-8"))

    def do_GET(self):
        query_params = parse.parse_qs(parse.urlsplit(self.path).query)
        print("query_params", query_params)
        query = query_params.get("q", None)
        if not query:
            self.__output_error("param q must be given")
            return
        vep_input = []
        for q in query:
            parts = q.split("_")
            if len(parts) == 4:
                if parts[3] in ["DEL", "DUP"]:
                    # Example structural variants
                    # VCF
                    # 1   160283      .   .   <DUP>   .   .   SVTYPE=DUP;END=471362    .
                    # 1   1385015     .   .   <DEL>   .   .   SVTYPE=DEL;END=1387562   .
                    # Ensembl
                    # 1    160283    471362    DUP  + sv1
                    # 1    1385015   1387562   DEL + sv2
                    # vep_input.append(
                    #     f"{parts[0]} {parts[1]} . . <{parts[3]}> . . SVTYPE={parts[3]};END={parts[2]}")
                    vep_input.append(f"{parts[0]} {parts[1]} {parts[2]} {parts[3]}")
                elif parts[1] > parts[2]:
                    # we have an insertion
                    vep_input.append("{} {} {} {}".format(*parts))
                else:
                    vep_input.append("{} {} . {} {}".format(*parts))
            elif len(parts) == 5:
                vep_input.append("{} {} {} {} {}".format(*parts))
            else:
                self.__output_error(
                    "wrong format in q parameter should be chr_position_ref_alt of chr_start_end_ref_alt"
                )
                return
        # print('vep_input', vep_input)
        vep_options = query_params.copy()
        vep_options = {
            k: False
            if v[0] in ["0", "false"]
            else True
            if v[0] in ["1", "true"]
            else v[0]
            for k, v in vep_options.items()
        }
        del vep_options["q"]
        print("vep_input", vep_input)
        print("vep_options", vep_options)
        vep_data = self.__run_vep(vep_input, **vep_options)
        # print('vep_data', vep_data)
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(vep_data).encode("utf-8"))
        return


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


if __name__ == "__main__":
    webServer = ThreadedHTTPServer(("0.0.0.0", 5005), Handler)
    print("Server started.")

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
