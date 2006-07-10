

from execute import execWithCapture, execWithCaptureErrorStatus, execWithCaptureStatus, execWithCaptureProgress, execWithCaptureErrorStatusProgress, execWithCaptureStatusProgress
from CommandError import *

import xml
import xml.dom
from xml.dom import minidom


class Cluster:
    
    def __init__(self):
        return
    
    def get_name(self):
        return self.__get_info()[0]
    
    def get_lock_type(self):
        return self.__get_info()[1]
    
    def get_nodes_num(self):
        return self.__get_info()[2]
    
    def __get_info(self):
        try:
            c_conf = minidom.parseString(file('/etc/cluster/cluster.conf').read(10000000)).firstChild
            name = c_conf.getAttribute('name')
            lock = None
            nodes_num = 0
            for node in c_conf.childNodes:
                if node.nodeType == xml.dom.Node.ELEMENT_NODE:
                    if node.nodeName == 'cman':
                        lock = 'dlm'
                    elif node.nodeName == 'gulm':
                        lock = 'gulm'
                    elif node.nodeName == 'clusternodes':
                        nodes = node
                        for node in nodes.childNodes:
                            if node.nodeType == xml.dom.Node.ELEMENT_NODE:
                                if node.nodeName == 'clusternode':
                                    nodes_num += 1
            if lock != None:
                return (name, lock, nodes_num)
        except:
            pass
        return (None, None, None)
    
    def running(self):
        if self.get_name() == None:
            return False
        try:
            args = ['/sbin/magma_tool', 'quorum']
            o, e, s = execWithCaptureErrorStatus('/sbin/magma_tool', args)
            if s == 0:
                if o.find('Quorate') != -1:
                    return True
        except:
            pass
        return False
