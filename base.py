# -*- coding: utf-8 -*-

def filter_networks(networks):
    for network in networks:
        if network.ref == 0:
            networks.remove(network)

def filter_pools(pools):
    for pool in pools:
        if len(pool.servers) == 0:
            pools.remove(pool)

def filter_servers(servers):
    for server in servers:
        if server.ref == 0:
            servers.remove(server)

def filter_hosts(hosts):
    for host in hosts:
        if host.ref == 0:
            hosts.remove(host)

class Network(object):
    def __init__(self, context, network):
        self._context = context
        self._dict = network
        self.subnets = network['subnets']
        self.name = network['name']
        self.ref = 0

class Pool(object):

    meters = ['network.services.lb.total.connections',
              'network.services.lb.active.connections',
              'network.services.lb.incoming.bytes',
              'network.services.lb.outgoing.bytes',
    ]

    def __init__(self, context, **kwargs):
        self._context = context
        self._dict = kwargs
        self.id = self._dict['id']
        self.name = self._dict['name']
        self.subnet_id = self._dict['subnet_id']
        self.provider = self._dict['provider']
        self.tenant_id = self._dict['tenant_id']

        self.net_name = None # should be set later by bind_network()
        self.servers = [] # should be set later by bind_servers()
        self.jumplink = {} # should be set later by bind_servers()

        self.statistics = {} # should be filled later by fetch_samples

        # get members
        self.members = []
        for member in self._dict['members']:
            body = self._context['q_client'].show_member(member)
            ip = body['member']['address']
            body = {'member' : {'weight' : body['member']['weight']}}
            self.members.append((ip, member, body))

    def bind_network(self, networks):
        for network in networks:
            for subnet in network.subnets:
                if subnet == self.subnet_id:
                    self.net_name = network.name
                    network.ref += 1
                    return

    def bind_servers(self, servers):
        for ip, _, body in self.members:
            for server in servers:
                if self.tenant_id == server.tenant_id:
                    for interface in server.interfaces:
                        for fix_ip in interface['fixed_ips']:
                            if ip == fix_ip['ip_address'] and self.subnet_id == fix_ip['subnet_id']:
                                self.servers.append((server, body['member']['weight']))
                                self.jumplink[server.id] = body
                                interface['pool'] = self
                                server.ref += 1

    def fetch_samples(self):
        client = self._context['c_client']
        for meter in self.meters:
            query = [dict(field='resource_id', op='eq', value=self.id)]
            samples = client.samples.list(meter_name=meter, limit=1, q=query)
            if len(samples) > 0:
                sample = samples[0].to_dict()
                self.statistics[meter] = (sample['counter_volume'], sample['timestamp'])

        #debug output
        print '#======= Pool information(%s) =======#' % (self.id)
        print self.statistics

class Server(object):

    meters = ['vcpus',
              'cpu_util',
              'memory',
              'memory.usage', # ?
              'disk.read.requests.rate',
              'disk.write.requests.rate',
              'disk.read.bytes.rate',
              'disk.write.bytes.rate',
              'disk.latency', # ?
              'disk.iops',    # ?
    ]

    interface_meters = ['network.incoming.bytes.rate',
                        'network.outgoing.bytes.rate',
                        'network.incoming.packets.rate',
                        'network.outgoing.packets.rate',
    ]

    def __init__(self, context, server):
        self._context = context
        self._dict = server.to_dict()
        self._server = server
        self.id = self._dict['id']
        self.network = server.networks
        self.tenant_id = self._dict['tenant_id']
        self.host_name = self._dict['OS-EXT-SRV-ATTR:host']
        self.server_name = self._dict['OS-EXT-SRV-ATTR:instance_name']
        self.ref = 0

        self.host = None # should be set later by bind_host
        self.statistics = {} # should be filled later by fetch_samples

        self.interfaces = [interface.to_dict() for interface in server.interface_list()]

    def bind_host(self, hosts):
        for host in hosts:
            if self.host_name == host.host_name:
                self.host = host
                host.servers.append(self)
                host.ref += 1

    def interface_name(self, port_id):
        return self.server_name + '-' + self.id + '-tap' + port_id[:11]

    def fetch_samples(self):
        client = self._context['c_client']
        for meter in self.meters:
            query = [dict(field='resource_id', op='eq', value=self.id)]
            samples = client.samples.list(meter_name=meter, limit=1, q=query)
            if len(samples) > 0:
                sample = samples[0].to_dict()
                self.statistics[meter] = (sample['counter_volume'], sample['timestamp'])

        for interface in self.interfaces:
            interface['statistics'] = {}
            for meter in self.interface_meters:
                source_name = self.interface_name(interface['port_id'])
                query = [dict(field='resource_id', op='eq', value=source_name)]
                samples = client.samples.list(meter_name=meter, limit=1, q=query)
                if len(samples) > 0:
                    sample = samples[0].to_dict()
                    interface['statistics'][meter] = (sample['counter_volume'], sample['timestamp'])

        print '#======= Server information(%s) =======#' % (self.id)
        print self.statistics

class Host(object):

    meters = ['compute.node.cpu.frequency',
              'compute.node.cpu.kernel.percent',
              'compute.node.cpu.idle.percent',
              'compute.node.cpu.user.percent',
              'compute.node.cpu.iowait.percent',
              'compute.node.cpu.percent',
    ]

    def __init__(self, context, host):
        self._dict = host.to_dict()
        self._host = host
        self._context = context
        self.host_name = self._dict['host_name']
        self.service = self._dict['service']
        self.zone = self._dict['zone']
        self.ref = 0

        self.servers = [] # should be set later by bind_host
        self.statistics = {} # should be filled later by fetch_samples

    def get_detail(self):
        if self._service == 'compute':
            # fetch host's description
            try:
                print self._context['n_client'].hosts.get(self._host_name)
            except Exception:
                pass

    def fetch_samples(self):
        client = self._context['c_client']
        for meter in self.meters:
            lable = '%s_%s' % (self.host_name, self.host_name)
            query = [dict(field='resource_id', op='eq', value=lable)]
            samples = client.samples.list(meter_name=meter, limit=1, q=query)
            if len(samples) > 0:
                sample = samples[0].to_dict()
                self.statistics[meter] = (sample['counter_volume'], sample['timestamp'])

        print '#=======  information(%s) =======#' % (self.host_name)
        print self.statistics
