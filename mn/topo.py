import os
import inspect

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.cli import CLI
from mininet.log import lg, info, setLogLevel
from mininet.node import Node, RemoteController, OVSSwitch, UserSwitch

setLogLevel('debug')


class MyTopo( Topo ):

    def __init__( self,):
        Topo.__init__( self )

        dpids = {
            'A': '1',
            'B': '2',
            'C': '3',
            'D': '4',
            'E': '5',
        }

        dr = {'defaultRoute': 'via 10.0.1.26'}
        hA = self.addHost('h1', ip='10.0.0.101/23', **dr)
        hC = self.addHost('h2', ip='10.0.0.102/23', **dr)
        hE = self.addHost('h3', ip='10.0.0.103/23', **dr)

        sA = self.addSwitch('A', dpid=dpids['A'])
        sB = self.addSwitch('B', dpid=dpids['B'])
        sC = self.addSwitch('C', dpid=dpids['C'])
        sD = self.addSwitch('D', dpid=dpids['D'])
        sE = self.addSwitch('E', dpid=dpids['E'])

        # Create links
        self.addLink('h1','A', intfName1='h1-eth1', intfName2='A-eth1')
        self.addLink('A','B', intfName1='A-eth2', intfName2='B-eth1')
        self.addLink('A','D', intfName1='A-eth3', intfName2='D-eth1')
        self.addLink('B', 'D', intfName1='B-eth2', intfName2='D-eth2')
        self.addLink('B','C', intfName1='B-eth3', intfName2='C-eth1')
        self.addLink('D','C', intfName1='D-eth3', intfName2='C-eth2')
        self.addLink('D', 'E', intfName1='D-eth4', intfName2='E-eth1')
        self.addLink('C','E', intfName1='C-eth3', intfName2='E-eth2')
        self.addLink('C','h2', intfName1='C-eth4', intfName2='h2-eth1')
        self.addLink('E','h3', intfName1='E-eth3', intfName2='h3-eth1')
        #


def startNetwork():

    IP = '127.0.0.1'
    ctrlPorts = {
        'A': 6633,
        'B': 6634,
        'C': 6635,
        'D': 6636,
        'E': 6637,
    }

    sA_ctrl = RemoteController( 'c0', ip=IP, port=ctrlPorts['A'])
    sB_ctrl = RemoteController( 'c1', ip=IP, port=ctrlPorts['B'])
    sC_ctrl = RemoteController( 'c2', ip=IP, port=ctrlPorts['C'])
    sD_ctrl = RemoteController( 'c3', ip=IP, port=ctrlPorts['D'])
    sE_ctrl = RemoteController( 'c4', ip=IP, port=ctrlPorts['E'])


    cmap = { 'A': sA_ctrl, 'B': sB_ctrl, 'C': sC_ctrl, 'D':sD_ctrl, 'E':sE_ctrl }

    class MultiSwitch( OVSSwitch ):
        "Custom Switch() subclass that connects to different controllers"

        def __init__(self, name, failMode='secure', datapath='kernel',
                     inband=False, protocols=None,
                     reconnectms=1000, stp=False, batch=False, **params):
            OVSSwitch.__init__(self, name, failMode=failMode, datapath=datapath,
                     inband=inband, protocols="OpenFlow13",
                     reconnectms=reconnectms, stp=stp, batch=batch, **params )

        def start( self, controllers ):
            return OVSSwitch.start( self, [ cmap[ self.name ] ] )

    topo = MyTopo()

    net = Mininet( topo=topo, switch=MultiSwitch, build=False )
    for c in [ sA_ctrl, sB_ctrl, sC_ctrl, sD_ctrl, sE_ctrl ]:
        net.addController(c)

    net.build()
    net.start()
    CLI( net )
    net.stop()


if __name__ == '__main__':
 # Get port numbers associated with names
 # ovs-vsctl -- --columns=name,ofport list Interface

 setLogLevel('debug')
 startNetwork()
