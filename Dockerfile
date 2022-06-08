FROM ensemblorg/ensembl-vep

# As the root user we install some additional software
USER root
RUN apt update && apt install -y python3
RUN ln -s /usr/bin/python3 /usr/bin/python
RUN perl INSTALL.pl -n -a p --PLUGINS all

# We switch back to user vep
USER vep
COPY ./app /app

# use python in unbuffered mode
ENV PYTHONUNBUFFERED=0

# We run the initial command
CMD /app/rest.py