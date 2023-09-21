FROM amazonlinux

WORKDIR /
RUN yum update -y
RUN yum install gcc gcc-c++ openssl-devel bzip2-devel libffi-devel wget tar gzip zip make zlib-devel -y

# Install Python 3.9
WORKDIR /
RUN wget https://www.python.org/ftp/python/3.9.17/Python-3.9.17.tgz
RUN tar -xzf Python-3.9.17.tgz
WORKDIR /Python-3.9.17
RUN ./configure --enable-optimizations
RUN make install

# Install Python 3.10
WORKDIR /
RUN wget https://www.python.org/ftp/python/3.10.13/Python-3.10.13.tgz
RUN tar -xzf Python-3.10.13.tgz
WORKDIR /Python-3.10.13
RUN ./configure --enable-optimizations
RUN make install

# Install Python 3.11
WORKDIR /
RUN wget https://www.python.org/ftp/python/3.11.4/Python-3.11.4.tgz
RUN tar -xzf Python-3.11.4.tgz
WORKDIR /Python-3.11.4
RUN ./configure --enable-optimizations
RUN make install

# Install Python packages and build zip files at runtime
WORKDIR /
COPY ./docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["3.9", "3.10", "3.11"]
