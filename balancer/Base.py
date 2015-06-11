# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod

class BaseBalancer(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def reweight(self, pools, networks, servers, hosts):
        pass
