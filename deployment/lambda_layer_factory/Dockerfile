FROM amazonlinux

VOLUME /packages
WORKDIR /packages
RUN yum update -y

# Install Python 3.7
RUN yum install python3 zip -y
RUN mkdir -p /packages/lambda_layer-python-3.7/python/lib/python3.7/site-packages

# Install Python 3.6
RUN yum groupinstall -y development
RUN yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
RUN yum install -y https://centos7.iuscommunity.org/ius-release.rpm
RUN yum install -y python36u
RUN yum install -y python36u-pip
RUN mkdir -p /packages/lambda_layer-python-3.6/python/lib/python3.6/site-packages

# Install Python packages and build zip files at runtime
COPY ./docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]
