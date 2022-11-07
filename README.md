# VEP Offline Rest

VEP Offline Rest is a docker container you can run to have VEP [https://www.ensembl.org/info/docs/tools/vep/index.html](Variant effect predictor) available as a rest service.

## Usage

To use the image make sure you have a populated vep cache then add the following service to the `docker-compose.yml` file

```yaml
version: '3'
services:
  vep_rest:
   image: dameyerdave/vep-offline-rest
   volumes:
     - '${HOME}/vep_data:/opt/vep/.vep'
   ports:
     - '5005:5005'
```

## API

The api is quite simple: use

```txt
http://localhost:5005/?q=11_119170358_A_G
```

to query the variant `chr_position_ref_alt` or `chr_start_end_ref_alt` or `chr_start_end_[DEL|DUP]`.

Additional VEP options can be defined as additional parameters (e.g. `&option=value`). The VEP options are documented in the VEP documentation.

To switch an option off use

```txt
option=0
```

To switch it on use

```txt
option=1
```

Default options are:

```txt
'use_given_ref': True,
'assembly': 'GRCh38',
'canonical': True,
'hgvs': True,
'hgvsg': True,
'symbol': True,
'xref_refseq': True,
'af_gnomad': True,
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
'af_gnomad': True,
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
'af_gnomad': True,
'max_af': True,
'pubmed': True,
'uniprot': True,
'mane': True,
'tsl': True,
'appris': True,
'variant_class': True,
'gene_phenotype': True,
'mirna': True,
```