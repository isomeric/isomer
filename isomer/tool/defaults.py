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

Contains database setup, certificate locations, platform details, service
templates and a table of exit codes for the management tool.

"""

import distro

distribution = distro.id().upper()

db_host_default = "127.0.0.1:27017"
db_host_help = "Define hostname for database server (default: " + db_host_default + ")"
db_host_metavar = "<ip:port>"

db_default = "isomer"
db_help = "Define name of database (default: " + db_default + ")"
db_metavar = "<name>"

source_url = "https://github.com/isomeric/isomer"

distribution_name = distro.codename()

node_source_list_docker = """
deb https://deb.nodesource.com/node_11.x sid main
deb-src https://deb.nodesource.com/node_11.x sid main
"""


platforms = {
    "Docker": {
        "pre_install": [
            [
                "sh",
                "-c",
                "wget --quiet -O - https://deb.nodesource.com/gpgkey/nodesource.gpg.key | sudo apt-key add -",
            ],
            {
                "action": "create_file",
                "filename": "/etc/apt/sources.list.d/nodesource.list",
                "content": node_source_list_docker,
            },
            ["apt-get", "update"],
        ],
        "post_install": [],
        "tool": ["apt-get", "install", "-y"],
        "packages": [
            "nodejs",
        ],
    },
    "Debian GNU/Linux": {
        "pre_install": [
            [
                "apt-get",
                "-y",
                "install",
                "apt-transport-https",
                "wget",
                "sudo",
                "gnupg",
                "gdebi-core",
                "python3",
                "python3-pip",
                "python3-spur",
                "virtualenv",
            ],
            [
                "sh",
                "-c",
                "wget --quiet -O - https://deb.nodesource.com/gpgkey/nodesource.gpg.key | sudo apt-key add -",
            ],
            ["apt-get", "update"],
            [
                "wget",
                "https://deb.nodesource.com/node_8.x/pool/main/n/nodejs/nodejs_8.15.1-1nodesource1_amd64.deb",
            ],
            ["gdebi", "-n", "nodejs_8.15.1-1nodesource1_amd64.deb"],
            [
                "wget",
                "http://httpredir.debian.org/debian/pool/main/m/mongodb/mongodb-server_3.4.18-2_all.deb",
            ],
            ["gdebi", "-n", "mongodb-server_3.4.18-2_all.deb"],
            [
                "wget",
                "http://httpredir.debian.org/debian/pool/main/m/mongodb/mongodb-server_3.4.18-2_all.deb",
            ],
            ["gdebi", "-n", "mongodb-server_3.4.18-2_all.deb"],
        ],
        "post_install": [["systemctl", "start", "mongodb.service"]],
        "tool": ["apt-get", "install", "-y"],
        "packages": [
            "python3-dev",
            "virtualenv",
            "git",
            "python3-bson",
            "python3-pymongo",
            "python3-pymongo-ext",
            "python3-bson-ext",
            "python3-cffi",
            "libffi-dev",
            "nginx-full",
            "libssl-dev",
            "certbot",
            "python3-certbot",
            "python3-certbot-nginx",
            "enchant",
        ],
    },
    "Ubuntu": "Debian GNU/Linux",
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

# noinspection PyPep8
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
    ssl_protocols TLSv1.2 TLSv1.3;
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
    "comment": "Isomer Remote Key",
}
