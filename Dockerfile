FROM ubuntu:latest

RUN apt-get update && apt-get install -y python-dev python-setuptools python-pip wget

RUN apt-get install --yes software-properties-common python-software-properties
RUN add-apt-repository ppa:ethereum/ethereum
RUN apt-get update
RUN apt-get install --yes solc

RUN wget http://gigaspaces-repository-eu.s3.amazonaws.com/org/cloudify3/get-cloudify.py

RUN apt-get install --yes python3-dev
RUN apt-get install --yes python3-pip

RUN pip3 install web3

RUN python get-cloudify.py --version 3.3.1

COPY nso /home/nso
COPY setup.py /home/setup.py

COPY cfgs /home/cfgs

RUN cd /home/nso/tosca/plugins/vnfm-cfy && python setup.py develop && cd -
RUN cd /home && python setup.py develop && cd -

RUN cp /home/cfgs/start.sh /etc/init.d/
RUN chmod +x /etc/init.d/start.sh

EXPOSE 8080