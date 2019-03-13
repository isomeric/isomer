#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Isomer - The distributed application framework
# ==============================================
# Copyright (C) 2011-2019 Heiko 'riot' Weinen <riot@c-base.org> and others.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""

Module: Defaults
================

Isomer distribution default settings.

Contains database setup, certificate locations, platform details, service templates and a table of exit codes for
the management tool.

"""

import distro

__author__ = "Heiko 'riot' Weinen"
__license__ = "AGPLv3"

distribution = 'DEBIAN'

db_host_default = '127.0.0.1:27017'
db_host_help = 'Define hostname for database server (default: ' + \
               db_host_default + ')'
db_host_metavar = '<ip:port>'

db_default = 'isomer'
db_help = 'Define name of database (default: ' + db_default + ')'
db_metavar = '<name>'

key_file = "/etc/ssl/certs/isomer/selfsigned.key"
cert_file = "/etc/ssl/certs/isomer/selfsigned.crt"
combined_file = "/etc/ssl/certs/isomer/selfsigned.pem"

source_url = 'https://github.com/isomeric/isomer'

distribution_name = distro.codename()

platforms = {
    'Debian GNU/Linux': {
        'pre_install':[
            ['apt-get', '-y', 'install', 'apt-transport-https', 'wget', 'sudo', 'gnupg', 'gdebi-core'],
            ['sh', '-c', 'wget --quiet -O - https://deb.nodesource.com/gpgkey/nodesource.gpg.key | sudo apt-key add -'],
            ['apt-get', 'update'],
            ['wget', 'https://deb.nodesource.com/node_8.x/pool/main/n/nodejs/nodejs_8.15.1-1nodesource1_amd64.deb'],
            ['gdebi', '-n', 'nodejs_8.15.1-1nodesource1_amd64.deb'],
            ['wget', 'http://httpredir.debian.org/debian/pool/main/m/mongodb/mongodb-server_3.4.18-2_all.deb'],
            ['gdebi', '-n', 'mongodb-server_3.4.18-2_all.deb'],
        ],
        'post_install': [['systemctl', 'start', 'mongodb.service']],
        'tool': ['apt-get', 'install', '-y'],
        'packages': [
            'python3', 'python3-pip', 'python3-dev', 'virtualenv', 'git',
            'python3-bson', 'python3-pymongo', 'python3-pymongo-ext', 'python3-bson-ext',
            'python3-cffi', 'libffi-dev',
            'nginx-full', 'libssl-dev', 'certbot', 'python3-certbot', 'python3-certbot-nginx',
            'enchant',
            # TODO: Kick out module dependencies (mostly gdal, grib and serial)
            'python3-grib', 'python3-serial', 'gdal-bin', 'python-gdal',
        ]
    },
    'Ubuntu': 'Debian GNU/Linux'
}

service_template = """[Unit]
Description=Isomer Node - {{instance}} ({{environment}})
After=network.target
Wants=mongodb.service

[Service]
Type=simple
User={{user_name}}
Group={{user_group}}
WorkingDirectory=/
ExecStart={{executable}}
StandardOutput=syslog
StandardError=syslog
Restart=True
KillSignal=SIGINT

[Install]
WantedBy=multi-user.target"""

nginx_template = """# DO NOT MODIFY THIS FILE BY HAND
# isomer manage tool maintains it automatically.
# Any changes you make here will probably be overwritten.

server {
    server_name {{server_public_name}};
    listen               80;

    rewrite ^/$ https://{{server_public_name}}/ redirect;

    location /.well-known/acme-challenge/ {
        alias /var/www/challenges/;
        try_files $uri =404;
    }
}

server {
    server_name {{server_public_name}};
    listen               443;
    ssl                  on;

    ssl_certificate      {{ssl_certificate}};
    ssl_certificate_key  {{ssl_key}};

    ssl_session_timeout 5m;
    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA:ECDHE-RSA-AES128-SHA:DHE-RSA-AES256-SHA:DHE-RSA-AES128-SHA;
    ssl_session_cache shared:SSL:50m;
    # ssl_dhparam /path/to/server.dhparam;
    ssl_prefer_server_ciphers on;

    keepalive_timeout    70;
    location / {
            proxy_pass      {{host_url}};
            include         proxy_params;
    }

    location /isomer-frontend {
        gzip_static on;

        alias /var/lib/isomer/{{instance}}/{{environment}}/frontend;
    }

    location /websocket {
        proxy_pass {{host_url}}websocket;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400s;
    }

    ### SERVICE DEFINITIONS ###
    ### SERVICE DEFINITIONS ###
}
"""

key_defaults = {
    "type": "rsa",
    "bits": 4096,
    "filename": "",
    "comment": "Isomer Remote Key"
}

EXIT_INVALID_ENVIRONMENT = 1
EXIT_INVALID_CONFIGURATION = 2
EXIT_INVALID_SOURCE = 3
EXIT_NO_PERMISSION = 5

EXIT_INSTALLATION_FAILED = 11
EXIT_PROVISIONING_FAILED = 12

EXIT_INSTANCE_EXISTS = 21
EXIT_INSTANCE_UNKNOWN = 22

EXIT_SERVICE_INVALID = 31

EXIT_USER_BAILED_OUT = 41

EXIT_NOTHING_TO_ARCHIVE = 51

EXIT_NO_CONFIGURATION = 61

EXIT_INVALID_PARAMETER = 62
EXIT_NO_CERTIFICATE = 63
