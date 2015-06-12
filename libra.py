# -*- coding: utf-8 -*-

from neutronclient.v2_0 import client as q_client
from novaclient.v2 import client as n_client
from ceilometerclient import client as c_client

import credentials
import base
from base import Pool
from base import Server
from base import Host
from base import Network

from balancer.RandomBalancer import RandomBalancer
from balancer.CPULPBalancer import CPULPBalancer

class LibraController(object):
    def __init__(self):
        self._q_client = q_client.Client(**credentials.get_q_creds())
        self._n_client = n_client.Client(**credentials.get_n_creds())
        self._c_client = c_client.get_client('2', **credentials.get_c_creds())
        self._context = {'q_client' : self._q_client,
                         'n_client' : self._n_client,
                         'c_client' : self._c_client,}

    def _get_all_pools(self):
        resp = self._q_client.list_pools()
        return [Pool(self._context, **pool) for pool in resp['pools']]

    def _get_all_servers(self):
        resp = self._n_client.servers.list(search_opts={'all_tenants' : True})
        return [Server(self._context, server) for server in resp]

    def _get_all_hosts(self):
        resp = self._n_client.hosts.list()
        return [Host(self._context, host) for host in resp if host.to_dict()['service'] == 'compute']

    def _get_all_networks(self):
        resp = self._q_client.list_networks()
        return [Network(self._context, network) for network in resp['networks']]

    def prepare(self):
        pools = self._get_all_pools()
        networks = self._get_all_networks()
        servers = self._get_all_servers()
        hosts = self._get_all_hosts()

        # associate things together
        for pool in pools:
            # order matters
            pool.bind_network(networks)
            pool.bind_servers(servers)

        for server in servers:
            server.bind_host(hosts)

        # remove irrelevant items
        base.filter_networks(networks)
        base.filter_pools(pools)
        base.filter_servers(servers)
        base.filter_hosts(hosts)

        # fetch statistics information
        for pool in pools:
            pool.fetch_samples()

        for server in servers:
            server.fetch_samples()

        for host in hosts:
            host.fetch_samples()

        return (pools, networks, servers, hosts)

    def balance(self):
        pools, networks, servers, hosts = self.prepare()

        # run algorithm
        balancer = CPULPBalancer()
        balancer.reweight(pools, networks, servers, hosts)

        # re-weight
        for pool in pools:
            for temp in pool.members:
                _, member, body = temp
                self._q_client.update_member(member, body)


if __name__ == '__main__':
    credentials.CFG.register_group(credentials.TGROUP)
    credentials.CFG(default_config_files=['libra.conf'])

    libra = LibraController()
    libra.balance()
