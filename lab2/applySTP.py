import json
import re
import time
import networkx
import requests
from mininet.cli import CLI
from mininet.log import MininetLogger
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.topo import Topo
from upload import put_flow


class MininetSimulator(object):

    def __init__(self, graph, controller_addr):
        self.graph = graph
        self.mininet_topo = Topo()
        self.controller_addr = controller_addr

    def generate_topo(self):
        nodes = self.graph.nodes()
        edges = self.graph.edges()
        hosts = [n for n in nodes if 1 == networkx.degree(self.graph, n)]
        for node in nodes:
            if node in hosts:
                self.mininet_topo.addHost(node)
            else:
                self.mininet_topo.addSwitch(node, protocols="OpenFlow13")
        for edge in edges:
            # set link properties here.
            # bw(Mbps), delay, loss, max_queue_size
            # source code is in {mininet_root}/mininet/link.py
            linkopts = dict()
            self.mininet_topo.addLink(edge[0], edge[1], **linkopts)

    def apply_stp(self):
        # 最小生成树
        self.graph = networkx.minimum_spanning_tree(self.graph)
        # 获取当前网络拓扑
        url = "http://172.16.86.1:8181/restconf/operational/network-topology:network-topology/topology/flow:1"
        rsp = requests.get(auth=("admin", "admin"), url=url)
        json_obj = json.loads(rsp.text)
        links = json_obj['topology'][0]['link']
        switch_state = {}

        for link in links:
            dest = re.findall(r"[-+]?\d+", link['destination']['dest-tp'])
            src = re.findall(r"[-+]?\d+", link['source']['source-tp'])
            print(f"s{src[0]}:{src[1]} and s{dest[0]}:{dest[1]}")
            if (f's{dest[0]}', f's{src[0]}') in self.graph.edges():
                if dest[0] not in switch_state:
                    switch_state[dest[0]] = set()
                if src[0] not in switch_state:
                    switch_state[src[0]] = set()
                switch_state[dest[0]].add(dest[1])
                switch_state[src[0]].add(src[1])
        for s in switch_state:
            # 为所有末端的路由器添加一个端口
            if len(switch_state[s]) == 1:
                switch_state[s].add('3')
            # 上传连通的流规则
            for in_port in switch_state[s]:
                out_ports = list(switch_state[s]-{in_port})
                put_flow("arp", s, in_port, out_ports)
                put_flow("ip", s, in_port, out_ports)
                print(f"s{s} {in_port} to {out_ports}")

    def run(self):
        self.generate_topo()
        net = Mininet(topo=self.mininet_topo,
                      controller=RemoteController,
                      build=False,
                      # autoStaticArp=True
                      )
        net.addController(ip=self.controller_addr)
        net.start()
        time.sleep(1)
        while(1):
            try:
                MS.apply_stp()
                break
            except Exception as e:
                print(e)
        CLI(net)
        net.stop()


MininetLogger().setLogLevel(levelname='debug')
g = networkx.read_graphml("task4_topo.graphml")
MS = MininetSimulator(g, "172.16.86.1")
MS.run()

