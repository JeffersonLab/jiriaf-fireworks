# Use an existing docker image as a base
FROM python:3.10


COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
# install ipython
RUN pip install ipython

RUN mkdir -p /fw/logs
COPY FireWorks/util /fw/util
COPY main /fw/main

# copy all files in the FireWorks directory to the container but keep the directory structure intact 
COPY FireWorks/jrm_launcher /fw/jrm_launcher
COPY FireWorks/launch-jrms.sh /fw/launch-jrms.sh

COPY create-ssh-connections/* /fw/create-ssh-connections/


ENTRYPOINT [ "/fw/launch-jrms.sh" ]