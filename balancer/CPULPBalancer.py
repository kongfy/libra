# -*- coding: utf-8 -*-

from Base import BaseBalancer
import pulp


class CPULPBalancer(BaseBalancer):
    def reweight(self, pools, networks, servers, hosts):
        prob = pulp.LpProblem('cpubalance', pulp.LpMinimize)
        t = pulp.LpVariable('T', lowBound = 0)
        prob += t

        vdict = {}
        for pool in pools:
            vlist = []
            total = 0.0
            for server, _ in pool.servers:
                cpu_util, _ = server.statistics['cpu_util']
                vcpus, _ = server.statistics['vcpus']
                total += cpu_util

                var = pulp.LpVariable(server.id, lowBound = 0)
                vlist.append(var)
                vdict[server.id] = var

                prob += var <= (vcpus * 100)

            prob += pulp.lpSum(vlist) == total

        for host in hosts:
            vlist = []
            for server in host.servers:
                vlist.append(vdict[server.id])
            prob += pulp.lpSum(vlist) <= t

        prob.solve()

        if prob.status != pulp.LpStatusOptimal:
            raise Exception('lp status wrong!')

        solution = {}

        print '#======= LP solution =======#'
        print("Status:", pulp.LpStatus[prob.status])
        for v in prob.variables():
            print v.name, '=', v.varValue
            solution[v.name] = max(int(v.varValue * 100), 1)

        for pool in pools:
            for server_id, body in pool.jumplink.items():
                body['member']['weight'] = solution[server_id.replace('-', '_')]
