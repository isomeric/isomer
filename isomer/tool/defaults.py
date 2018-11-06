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

source_url = 'https://github.com/hackerfleet/hfos'

EXIT_INVALID_ENVIRONMENT = 1
EXIT_INVALID_CONFIGURATION = 2
EXIT_INVALID_SOURCE = 3

EXIT_INSTALLATION_FAILED = 11
EXIT_PROVISIONING_FAILED = 12

EXIT_INSTANCE_EXISTS = 21
EXIT_INSTANCE_UNKNOWN = 22

EXIT_SERVICE_INVALID = 31

EXIT_USER_BAILED_OUT = 41

EXIT_NOTHING_TO_ARCHIVE = 51
