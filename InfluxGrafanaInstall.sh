#!/bin/bash

sudo apt update
sudo apt upgrade -y
sudo apt install curl

#install InfluxDB v1.8.9
wget https://dl.influxdata.com/influxdb/releases/influxdb_1.8.9_amd64.deb
sudo dpkg -i influxdb_1.8.9_amd64.deb

sudo systemctl unmask influxdb
sudo systemctl enable influxdb
sudo systemctl start influxdb

#configure influxdb
influx -execute "create user admin with password 'influxadmin' with all privileges"
influx -execute "create database sensor_data"
influx -execute "use sensor_data"
influx -execute "create user rpi with password 'rpiinflux'"
influx -execute "grant all on sensor_data to rpi"
influx -execute "create user grafana with password 'grafana'"
influx -execute "grant read on sensor_data to grafana"
influx -execute "create retention policy ninety_days on sensor_data duration 90d replication 1 default"

#install grafana
sudo apt-get install -y apt-transport-https
sudo apt-get install -y software-properties-common wget
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list
sudo apt update
sudo apt install grafana -y

sudo systemctl daemon-reload
sudo systemctl enable grafana-server
sudo systemctl start grafana-server

#forward port 3000 for grafana remote access
sudo ufw disable
sudo ufw allow 3000
sudo ufw enable

echo "InfluxDB and Grafana have been installed"
echo "It is HIGHLY recommended to change the passwords of the default accounts created in InfluxDB"
echo "This can be done with the command <influx -execute \"set passwd [account name]\"> "
