from collections import deque
from operator import attrgetter
#from umit.pm.gui.plugins.atoms import Version
from atoms import Version

class Graph():
    def __init__(self, lst=[]):
        self._list = lst

    def clone(self):
        return Graph(self._list[:])
    
    def append(self,node):
        self._list.append(node)        

    def get_by_name(self, value):
        for node in self._list:
            if node.name == value:
                return node

    def _check_validity(self, provide, need):
        if provide[0] != need[0]:
            return False

        print "\tChecking", provide, need

        need_str, need_op, need_ver = need
        prov_str, prov_op, prov_ver = provide

        return need_op(prov_ver, need_ver)

    def _has_conflicts(self, load_list, target):
        for conf in target.conflicts:
            conf_str, conf_op, conf_ver = conf

            print conf

            for node in load_list:
                for provide in node.provides:
                    prov_str, prov_op, prov_ver = provide

                    print conf_str, prov_str

                    if conf_str != prov_str:
                        continue

                    if conf_op(prov_ver, conf_ver):
                        return True
        return False



    def remove_conflicts_for(self, target):
        for conf in target.conflicts:
            conf_str, conf_op, conf_ver = conf

            print conf

            for node in self._list:
                for provide in node.provides:
                    prov_str, prov_op, prov_ver = provide

                    print conf_str, prov_str

                    if conf_str != prov_str:
                        continue

                    if conf_op(prov_ver, conf_ver):
                        print "Removing Conflict Node: ",node
                        self._list.remove(node)

    def _add_to_queue(self, target, queue):
        if target not in queue:
            queue.append(target)

    def get_dep_for(self, start, queue=None, load_list=None):
        if queue is None:
            node = self.get_by_name(start)

            queue = deque()
            queue.append(node)

        if load_list is None:
            load_list = []

        while queue:
            node = queue.popleft()

            self.remove_conflicts_for(node)

            for need in node.needs:
                first_stage = []

                for target in self._list:
                    for provide in target.provides:
                        if self._check_validity(provide, need):
                            first_stage.append(target)
                            continue

                if not first_stage:
                    print "No dep matching your needs", need
                    return []

                elif len(first_stage) == 1:
                    self._add_to_queue(first_stage[0],queue)

                elif len(first_stage) > 1:
                    print "Multiple dep matching your needs", need
                    print "\t", first_stage


                    # TODO: Create a sort function that uses atoms.py to replace sorted.
                    
                    first_stage = sorted(first_stage, key=attrgetter('provides'), reverse=True)
                    
                    print "Sorted", first_stage

                    for target in first_stage:
                        fake_graph = Graph(lst=list(self._list))
                        fake_graph.remove_conflicts_for(target)
                        part_list = fake_graph.get_dep_for(target.name)

                        print "Partial: ", part_list
                        if not part_list:
                            continue

                        self._add_to_queue(target,queue)
                        break

            if node not in load_list:
                load_list.append(node)
        return load_list

class Node(object):
    def __init__(self, name, conflicts, needs, provides):
        """
        @param name an identification string for the plugin
        @param conflicts a list of conflict VersionString ['=ftp-lib-1.0', ..]
        @param needs a list of need VersionString
        @param provides a list of provide VersionString
        """
        self.name = name
        self.conflicts = [Version.extract_version(item) for item in conflicts]
        self.provides  = [Version.extract_version(item) for item in provides]
        self.needs   = [Version.extract_version(item) for item in needs]

    def __repr__(self):
        return "Node: %s %s" % (self.name, str(self.provides))

class DepSolver(object):
    """
    This class solve plugin dependencies and conflicts.
    Is called before the startup of plugins and generate a DAG with dependencie of each plugin loaded.

    Is only for test
    """
    def __init__(self):
        self.dep_path = []

        # This graph should be static so you cannot call at any time remove_*
        # stuff.
        self.graph = Graph()

    def load_dependences(self, path):
        self.graph.append(
            Node('SMBDissector', ['=vnc-1.0', '>mysql-1.0'], ['>tcp-1.0', '<udp-2.0'], [])
        )
        self.graph.append(
            Node('MySQLDissector', [], [], ['=mysql-1.1'])
        )
        self.graph.append(
            Node('TCPDecoder', [], ['>ip-1.0'], ['=tcp-1.1'])
        )
        self.graph.append(
            Node('TCPDecoder2', [], ['>ip-1.0'], ['=tcp-1.1.2'])
        )
        self.graph.append(
            Node('TCPDecoder3', [], ['>ip-1.0'], ['=tcp-2.0'])
        )
        self.graph.append(
            Node('TCPDecoder4', [], ['>ip-1.0'], ['=tcp-2.0.1'])
        )
        self.graph.append(
            Node('ShinyTCP', ['=eth-1.7'], ['>ip-1.0'], ['=tcp-1.6'])
        )
        self.graph.append(
            Node('UDPDecoder', ['=tcp-1.1'], ['>ip-1.0'], ['=udp-1.5'])
        )
        self.graph.append(
            Node('IPDecoder', [], ['>eth-1.0'], ['=ip-1.5'])
        )
        self.graph.append(
            Node('EthDecoder', [], [], ['=eth-1.7'])
        )

        self.graph.append(
            Node('ShinyETH', [], [], ['>eth-1.7'])
        )

    def get_dep_for(self, start):
        orig = self.graph.clone()
        print orig.get_dep_for(start)
        
        print "Cloned Graph: ", orig._list
        print "Main Graph: ", self.graph._list

#main
if __name__ == '__main__':
    dep = DepSolver()
    dep.load_dependences("/usr/src/umit/packet-manipulator/audits/compiled")
    dep.get_dep_for("SMBDissector")
