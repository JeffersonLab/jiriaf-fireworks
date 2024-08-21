# Use an existing docker image as a base
FROM python:3.10


COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

RUN mkdir -p /fw/logs
COPY FireWorks/util /fw/util
COPY main /fw/main

# copy all files in the FireWorks directory to the container but keep the directory structure intact 
COPY FireWorks/components /fw/components
COPY FireWorks/launch-jrms.sh /fw/launch-jrms.sh
COPY FireWorks/gen_wf.py /fw/gen_wf.py
COPY FireWorks/__init__.py /fw/__init__.py
COPY FireWorks/create_config.sh /fw/create_config.sh

COPY create-ssh-connections/* /fw/create-ssh-connections/


ENTRYPOINT [ "/fw/launch-jrms.sh" ]