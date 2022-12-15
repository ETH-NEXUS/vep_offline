ARG VEP_VERSION

FROM ensemblorg/ensembl-vep:release_${VEP_VERSION}

# no interaction during debian installations
ARG DEBIAN_FRONTEND=noninteractive

# use python in unbuffered mode
ENV PYTHONUNBUFFERED=1

# This is the volume of the vep data
VOLUME /opt/vep/.vep

# As the root user we install some additional software
USER root
RUN apt-get update && apt-get install -y python3 python3-pip rsync libgd-perl
RUN ln -s /usr/bin/python3 /usr/bin/python
RUN python -m pip install --disable-pip-version-check --upgrade pip

RUN perl INSTALL.pl -n -a p --PLUGINS all

# We switch back to user vep
USER vep

# Copy the stuff over
COPY ./app /app

# Set the working directory to /app
WORKDIR /app

# Install the python requirements
RUN pip install -r ./requirements.txt

ENTRYPOINT [ "./entrypoint.sh" ]