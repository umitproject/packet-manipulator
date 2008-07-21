#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2006 Insecure.Com LLC.
# Copyright (C) 2007-2008 Adriano Monteiro Marques
#
# Author: Adriano Monteiro Marques <adriano@umitproject.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import cPickle

from umitCore.ServicesDump import services_dump_file

def load_dumped_services():
    serv_dump = open(services_dump_file, "rb")
    services_list = cPickle.load(serv_dump)
    serv_dump.close()

    return services_list


class ServiceList(object):
    def __init__(self):
        self.services = load_dumped_services()

    def get_service(self, service_name):
        try:
            return Service(service_name, self.services[service_name])
        except:
            return None

    def get_services_list(self):
        return self.services.keys()


class Service(object):
    def __init__(self, service_name, service_dict):
        self.ports = service_dict["ports"]
        self.comment = service_dict["comment"]
        self.tcp = service_dict["tcp"]
        self.udp = service_dict["udp"]
        self.ddp = service_dict["ddp"]
        self.service_name = service_name


if __name__ == "__main__":
    s = ServiceList()
    print s.services
