# Use an existing docker image as a base
FROM jlabtsai/jrm-fw:latest


COPY FireWorks/util /fw/util


ENTRYPOINT [ "/fw/main.sh" ]