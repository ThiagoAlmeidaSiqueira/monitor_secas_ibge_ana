#!/bin/bash
sudo yum install -y docker
sudo mkdir -p /opt/monitorDeSecas/
sudo chmod 755 -R /opt/monitorDeSecas/
sudo chown root:root -R /opt/monitorDeSecas/
sudo docker build . -t monitor_de_secas
sudo docker run -v /opt/monitorDeSecas/saida:/opt/monitorDeSecas/saida monitor_de_secas

#sudo docker run monitor_de_secas