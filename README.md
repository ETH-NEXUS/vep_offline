# VEP Offline

VEP Offline Rest is a docker container you can run to have VEP [https://www.ensembl.org/info/docs/tools/vep/index.html](Variant effect predictor) available as a rest service.

## Usage

To use the image make sure you have a populated vep cache then add the following service to the `docker-compose.yml` file

```yaml
version: '3'
services:
  vep_rest:
    image: ethnexus/vep_offline
    volumes:
      - '${HOME}/vep_data:/opt/vep/.vep'
    ports:
      - '5005:5005'
    env_file:
      - .env
    command:
      - rest
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
'af': True,
'af_1kg': True,
'af_gnomad': True,
'appris': True,
'assembly': 'GRCh38',
'biotype': True,
'cache': True,
'canonical': True,
'ccds': True,
'domains': True,
'flag_pick': True,
'force_overwrite': True,
'gene_phenotype': True,
'hgvs': True,
'hgvsg': True,
'json': True,
'mane': True,
'max_af': True,
'merged': True,
'mirna': True,
'numbers': True,
'offline': True,
'polyphen': 'b',
'protein': True,
'pubmed': True,
'regulatory': True,
'shift_3prime': '1',
'shift_genomic': '1',
'shift_length': True,
'show_ref_allele': True,
'sift': 'b',
'symbol': True,
'tsl': True,
'uniprot': True,
'use_given_ref': True,
'var_synonyms': True,
'variant_class': True,
'xref_refseq': True
```

## Run any VEP command

You can also use this docker image to run vep locally with whatever parameters you want:

```bash
docker run --rm vep_offline vep <your parameters>
```
