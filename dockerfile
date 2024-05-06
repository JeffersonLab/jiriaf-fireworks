# Use an existing docker image as a base
FROM jlabtsai/jrm-fw:latest


COPY FireWorks/util /fw/util

COPY FireWorks/create_config.sh /fw/create_config.sh
COPY FireWorks/gen_wf.py /fw/gen_wf.py
COPY FireWorks/main.sh /fw/main.sh
COPY FireWorks/my_launchpad.yaml /fw/my_launchpad.yaml

ENTRYPOINT [ "/fw/main.sh" ]