#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# isomer - Hackerfleet Operating System
# ===================================
# Copyright (C) 2011-2018 Heiko 'riot' Weinen <riot@c-base.org> and others.
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

__author__ = "Heiko 'riot' Weinen"
__license__ = "AGPLv3"

distribution = 'DEBIAN'
service_template = 'isomer.service'

db_host_default = '127.0.0.1:27017'
db_host_help = 'Define hostname for database server (default: ' + \
               db_host_default + ')'
db_host_metavar = '<ip:port>'

db_default = 'isomer'
db_help = 'Define name of database (default: ' + db_default + ')'
db_metavar = '<name>'

nginx_configuration = 'nginx.conf'
key_file = "/etc/ssl/certs/isomer/selfsigned.key"
cert_file = "/etc/ssl/certs/isomer/selfsigned.crt"
combined_file = "/etc/ssl/certs/isomer/selfsigned.pem"

source_url = 'https://github.com/isomeric/isomer'

platforms = {
    'Debian GNU/Linux': {
        'pre_install': [
            ['apt-get', '-y', 'install', 'apt-transport-https', 'wget'],
            ['sh', '-c', 'wget --quiet -O - https://deb.nodesource.com/gpgkey/nodesource.gpg.key | sudo apt-key add -'],
            ['sh', '-c', 'VERSION=node_8.x ; '
                         'DISTRO="$(lsb_release -s -c)" ; '
                         'echo "deb https://deb.nodesource.com/$VERSION $DISTRO main" | '
                         'sudo tee /etc/apt/sources.list.d/nodesource.list'
             ],
            ['apt-get', 'update'],
        ],
        'post_install': [['systemctl', 'start', 'mongodb.service']],
        'tool': ['apt-get', 'install', '-y'],
        'packages': [
            'mongodb', 'python3', 'python3-pip', 'python3-grib',
            'python3-bson', 'python3-pymongo', 'python3-serial',
            'python3-pymongo-ext', 'python3-bson-ext', 'python3-dev',
            'python3-cffi', 'libffi-dev', 'libssl-dev',
            'nodejs', 'enchant', 'nginx-full', 'virtualenv', 'git',
            'gdal-bin', 'python-gdal', 'nodejs'
        ]  # TODO: Kick out module dependencies (mostly gdal, grib and serial)
    },
    'Ubuntu': 'Debian GNU/Linux'
}

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
