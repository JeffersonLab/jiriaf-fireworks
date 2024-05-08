# Use an existing docker image as a base
FROM python:3.10


COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

RUN mkdir -p /fw/logs
COPY FireWorks/util /fw/util
COPY FireWorks/main /fw/main

COPY FireWorks/create_config.sh /fw/create_config.sh
COPY FireWorks/gen_wf.py /fw/gen_wf.py
COPY FireWorks/launch-jrms.sh /fw/launch-jrms.sh

ENTRYPOINT [ "/fw/launch-jrms.sh" ]