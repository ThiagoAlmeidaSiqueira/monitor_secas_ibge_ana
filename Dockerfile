FROM centos:latest
LABEL poject="Monitor de Seca dos municípios"
LABEL maintainer "thiagoalmeidasiqueira@gmail.com"
#ENV LC_ALL=en_US.UTF-8
#ENV LANG=en_US.UTF-8cd /opt/monitorDeSecas	
#ENV LANGUAGE=en_US.UTF-8
RUN mkdir -p /opt/monitorDeSecas/
ADD monitorDeSecas.py /opt/monitorDeSecas/
RUN yum -y install python2-pip --nogpgcheck \
    && yum clean all \
    && pip2 install --no-cache-dir lxml requests shapely xlrd shapely[vectorized] fiona 
WORKDIR "/opt/monitorDeSecas"
RUN pwd
CMD [ "python2","-u", "/opt/monitorDeSecas/monitorDeSecas.py" ]
#CMD ["/bin/bash"]