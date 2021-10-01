import sys
import networkx
import random
from mininet.log import MininetLogger
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import TCLink
from mininet.node import RemoteController
from mininet.cli import CLI


# avoid IP conflict
def convert_to_ip(n):
    return '10.0.' + str((int(n) + 1) // 256) + '.' + str((int(n) + 1) % 256)


# avoid MAC conflict
def convert_to_mac(n):
    return '12:34:56:78:' + '%02X' % ((int(n) + 1) // 256) + ':' + '%02X' % ((int(n) + 1) % 256)


class MininetSimulator(object):

    def __init__(self, graph, controller_addr, seed=1234567):
        self.graph = graph
        self.random = random.Random(seed)
        self.mininet_topo = Topo()
        self.controller_addr = controller_addr

    def generate_topo(self):
        nodes = self.graph.nodes()
        edges = self.graph.edges()
        hosts = [n for n in nodes if 1 == networkx.degree(self.graph, n)]
        for node in nodes:
            if node in hosts:
                self.mininet_topo.addHost(node, ip=convert_to_ip(node), mac=convert_to_mac(node))
            else:
                self.mininet_topo.addSwitch(node, protocols="OpenFlow13")
        if len(hosts) == 0:
            for node in nodes:
                self.mininet_topo.addHost("host%s" % node, ip=convert_to_ip(node), mac=convert_to_mac(node))
                self.mininet_topo.addLink("host%s" % node, node)
        for edge in edges:
            # set link properties here.
            # bw(Mbps), delay, loss, max_queue_size
            # source code is in {mininet_root}/mininet/link.py
            linkopts = dict()
            self.mininet_topo.addLink(edge[0], edge[1], **linkopts)

    def run(self):
        self.generate_topo()
        net = Mininet(topo=self.mininet_topo,
                      controller=RemoteController,
                      link=TCLink,
                      build=False,
                      # autoStaticArp=True
                      )
        net.addController(ip=self.controller_addr)

        net.start()
        CLI(net)
        net.stop()


def main():
    MininetLogger().setLogLevel(levelname='info')
    filename = sys.argv[1]
    g = networkx.read_graphml(filename)
    MS = MininetSimulator(g, sys.argv[2])
    MS.run()


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: " + sys.argv[0] + "[GRAPHML_FILE]" + "[CONTROLLER_ADDR]")
        sys.exit()
    main()
