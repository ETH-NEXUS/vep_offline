FROM ensemblorg/ensembl-vep:release_106.1

# As the root user we install some additional software
USER root
RUN apt update && apt install -y python3 libgd-perl
RUN ln -s /usr/bin/python3 /usr/bin/python
RUN perl INSTALL.pl -n -a p --PLUGINS all

# We switch back to user vep
USER vep
COPY ./app /app

# use python in unbuffered mode
ENV PYTHONUNBUFFERED=1

# We run the initial command
CMD /app/rest.py