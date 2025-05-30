FROM public.ecr.aws/amazonlinux/amazonlinux:2023-minimal
RUN ln -s /usr/bin/microdnf /usr/bin/yum

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

# Update pip and setuptools for all Python versions - use explicit version to ensure consistency
RUN python3.9 -m pip install --upgrade pip setuptools==78.1.1
RUN python3.10 -m pip install --upgrade pip setuptools==78.1.1
RUN python3.11 -m pip install --upgrade pip setuptools==78.1.1

# ── 2️⃣ tell pip to refuse silent downgrades later ──────────────
ENV PIP_UPGRADE_STRATEGY=eager

# Install Python packages and build zip files at runtime
WORKDIR /
COPY ./docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["3.9", "3.10", "3.11"]
