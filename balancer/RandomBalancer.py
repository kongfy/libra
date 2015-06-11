# -*- coding: utf-8 -*-

from Base import BaseBalancer
import random

class RandomBalancer(BaseBalancer):
    def reweight(self, pools, networks, servers, hosts):
        for pool in pools:
            for temp in pool.members:
                _, _, body = temp
                body['member']['weight'] = random.randint(1, 10)
