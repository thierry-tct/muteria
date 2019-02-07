import logging
import enum
import collections

import networkx

import muteria.common.mix as common_mix

ERROR_HANDLER = common_mix.ErrorHandler()

# TODO Find way to make the classes so that new elements cannot be added on the fly

class EnumAutoName(enum.Enum):
    # This function do not have 'self'
#    def _generate_next_value_(name, start, count, last_values):
#        return name

    def get_str(self):
        return self.name

    @classmethod
    def has_element_named(cls, e_name):
        return ename in cls.__members__
#~ class EnumAutoName

@enum.unique
class Tasks(EnumAutoName):
    STARTING = 0 #enum.auto()

    TESTS_GENERATION = 1 #enum.auto()
    TESTS_SELECTION_PRIORITIZATION = 2 #enum.auto()
    PASS_FAIL_TESTS_EXECUTION = 3 #enum.auto()

    CODE_SCOPE_GENERATION = 4 #enum.auto()
    CODE_SCOPE_SELECTION_PRIORITIZATION = 5 #enum.auto()
    CODE_COVERAGE_TESTS_EXECUTION = 6 #enum.auto()

    MUTANTS_GENERATION = 7 #enum.auto()

    MUTANTS_SELECTION_PRIORITIZATION = 8 #enum.auto()

    MUTANT_COVERAGE_TESTS_EXECUTION = 9 #enum.auto()
    WEAK_MUTATION_TESTS_EXECUTION = 10 #enum.auto()
    STRONG_MUTATION_TESTS_EXECUTION = 11 #enum.auto()

    PASS_FAIL_STATS = 12 #enum.auto()
    CODE_COVERAGE_STATS = 13 #enum.auto()
    MUTANT_COVERAGE_STATS = 14 #enum.auto()
    WEAK_MUTATION_STATS = 15 #enum.auto()
    STRONG_MUTATION_STATS = 16 #enum.auto()
    AGGREGATED_STATS = 17 #enum.auto()

    FINISHING = 18 #enum.auto()
#~ class Tasks

@enum.unique
class Status(EnumAutoName):
    UNTOUCHED = -1 #enum.auto()
    EXECUTING = 0 #enum.auto()
    DONE = 1 #enum.auto()
    
    @classmethod
    def is_valid(cls, elem):
        return elem in cls
#~ class Status

class TaskOrderingDependency(object): 
    '''
    The task dependency structure is following(Teh structure neve change):
    ----------------------------------------------------------------------
        CODE_SCOPE_GENERATION --> STARTING
        TESTS_GENERATION --> STARTING
        MUTANTS_GENERATION --> STARTING

        TESTS_SELECTION_PRIORITIZATION --> TESTS_GENERATION

        PASS_FAIL_TESTS_EXECUTION --> TESTS_SELECTION_PRIORITIZATION

        MUTANTS_SELECTION_PRIORITIZATION --> MUTANTS_GENERATION 

        CODE_SCOPE_SELECTION_PRIORITIZATION --> CODE_SCOPE_GENERATION

                                          | CODE_SCOPE_SELECTION_PRIORITIZATION
        CODE_COVERAGE_TESTS_EXECUTION --> | PASS_FAIL_TESTS_EXECUTION

                                            | MUTANTS_SELECTION_PRIORITIZATION
        MUTANT_COVERAGE_TESTS_EXECUTION --> | PASS_FAIL_TESTS_EXECUTION

                                          | MUTANTS_SELECTION_PRIORITIZATION
        WEAK_MUTATION_TESTS_EXECUTION --> | PASS_FAIL_TESTS_EXECUTION

                                            | CODE_COVERAGE_TESTS_EXECUTION
        STRONG_MUTATION_TESTS_EXECUTION --> | WEAK_MUTATION_TESTS_EXECUTION
                                            | MUTANT_COVERAGE_TESTS_EXECUTION

        PASS_FAIL_STATS --> PASS_FAIL_TESTS_EXECUTION

        CODE_COVERAGE_STATS --> CODE_COVERAGE_TESTS_EXECUTION

        MUTANT_COVERAGE_STATS --> MUTANT_COVERAGE_TESTS_EXECUTION

        WEAK_MUTATION_STATS --> WEAK_MUTATION_TESTS_EXECUTION

        STRONG_MUTATION_STATS --> STRONG_MUTATION_TESTS_EXECUTION
        
                             | PASS_FAIL_STATS
                             | CODE_COVERAGE_STATS
        AGGREGATED_STATS --> | MUTANT_COVERAGE_STATS
                             | WEAK_MUTATION_STATS
                             | STRONG_MUTATION_STATS

        FINISHING --> AGGREGATED_STATS
    ------------------------------------------------------------------------

    '''
    def __init__(self, json_obj=None):
        if json_obj is None:
            self.initialize_data_graph()
        else:
            # Check that every task is present
            if type(json_obj) != dict:
                logging.error("{} {}".format("Invalid object to initialize", \
                                "TaskOrderingDependency, must be a 'dict'"))
                ERROR_HANDLER.error_exit_file(__file__)
            if len(json_obj) != len(Tasks):
                logging.error("{} {}".format("Invalid object to initialize", \
                                "TaskOrderingDependency. Size mismatch"))
                ERROR_HANDLER.error_exit_file(__file__)
            # verify
            for key_t in Tasks:
                if key_t.get_name() not in json_obj:
                    logging.error("{} {} {} {}".format( \
                        "Invalid object to initialize TaskOrderingDependency", \
                        "The task", key_t.get_name(), "is absent in json_obj"))
                    ERROR_HANDLER.error_exit_file(__file__)
                if not Status.has_element_named(json_obj[key_t.get_name()]):
                    logging.error("{} {} {} {}".format( \
                        "Invalid object to initialize TaskOrderingDependency", \
                        "The task", key_t.get_name(), "has invalid status"))
                    ERROR_HANDLER.error_exit_file(__file__)
            # initialize
            decoded_json_obj = {}
            for k_str, v_str in json_obj.iteritems():
                decoded_json_obj[Tasks[k_str]] = Status[v_str]
            self.initialize_data_graph(decoded_json_obj)
    #~ def __init__()

    def get_as_json_object(self):
        ret_obj = {}
        for key_t in Tasks:
            ret_obj[key_t.get_name()] = \
                            self._lookup_task_cell(key_t).get_status().get_name()
        return ret_obj
    #~ def get_as_json_object()

    def export_graph(self, graph_out_filename):
        graph = networkx.Graph()
        # add nodes
        for key_t in Tasks:
            graph.add_node(key_t.get_name())
        # add edges
        visited = set()
        queue = collections.deque()
        visited.add(self.root)
        queue.append(self.root)
        while queue:
            cur_node = queue.popleft()
            for d in cur_node.get_dependencies():
                graph.add_edge(d.get_task_name().get_name(), \
                                        cur_node.get_task_name().get_name())
                if d not in visited:
                    visited.add(d)
                    queue.append(d)
        # print graph
        d_graph = networkx.DiGraph(graph) 
        networkx.write_graphml(d_graph, graph_out_filename)
    #~ def export_graph()

    def initialize_data_graph(self, task_status_map=None):
        '''
        Each param is the status of the corresponding task 
        '''
        # Default behaviour (initial initialization)
        if task_status_map is None:
            task_status_map = {}
            for key_t in Tasks:
                task_status_map[key_t] = Status.UNTOUCHED

        # set the root cell (The root has no uses)
        finishing = self.Cell(Tasks.FINISHING)
        finishing.set_status(finishing)

        self.root = finishing

        # Construct the rest of the dependence graph, starting at the root
        ## Stats Layer
        ### Aggregate stats
        agg_stats =  self.Cell(Tasks.AGGREGATED_STATS)
        agg_stats.set_status(task_status_map(Tasks.AGGREGATED_STATS))        
        finishing.add_dependency(agg_stats)

        ### Other stats
        passfail_stats = self.Cell(Tasks.PASS_FAIL_STATS)
        passfail_stats.set_status(task_status_map(Tasks.PASS_FAIL_STATS))
        agg_stats.add_dependency(passfail_stats)

        cc_stats = self.Cell(Tasks.CODE_COVERAGE_STATS)
        cc_stats.set_status(task_status_map(Tasks.CODE_COVERAGE_STATS))
        agg_stats.add_dependency(cc_stats)

        mc_stats = self.Cell(Tasks.MUTANT_COVERAGE_STATS)
        mc_stats.set_status(task_status_map(Tasks.MUTANT_COVERAGE_STATS))
        agg_stats.add_dependency(mc_stats)

        wm_stats = self.Cell(Tasks.WEAK_MUTATION_STATS)
        wm_stats.set_status(task_status_map(Tasks.WEAK_MUTATION_STATS))
        agg_stats.add_dependency(wm_stats)

        sm_stats = self.Cell(Tasks.STRONG_MUTATION_STATS)
        sm_stats.set_status(task_status_map(Tasks.STRONG_MUTATION_STATS))
        agg_stats.add_dependency(sm_stats)

        ## Matrices Layer
        sm = self.Cell(Tasks.STRONG_MUTATION_TESTS_EXECUTION)
        sm.set_status(task_status_map(Tasks.STRONG_MUTATION_TESTS_EXECUTION))
        sm_stats.add_dependency(sm)

        cc = self.Cell(Tasks.CODE_COVERAGE_TESTS_EXECUTION)
        cc.set_status(task_status_map(Tasks.CODE_COVERAGE_TESTS_EXECUTION))
        cc_stats.add_dependency(cc)
        sm.add_dependency(cc)

        mc = self.Cell(Tasks.MUTANT_COVERAGE_TESTS_EXECUTION)
        mc.set_status(task_status_map(Tasks.MUTANT_COVERAGE_TESTS_EXECUTION))
        mc_stats.add_dependency(mc)
        sm.add_dependency(mc)

        wm = self.Cell(Tasks.WEAK_MUTATION_TESTS_EXECUTION)
        wm.set_status(task_status_map(Tasks.WEAK_MUTATION_TESTS_EXECUTION))
        wm_stats.add_dependency(wm)
        sm.add_dependency(wm)

        passfail = self.Cell(Tasks.PASS_FAIL_TESTS_EXECUTION)
        passfail.set_status(task_status_map(Tasks.PASS_FAIL_TESTS_EXECUTION))
        passfail_stats.add_dependency(passfail)
        cc.add_dependency(passfail)
        mc.add_dependency(passfail)
        wm.add_dependency(passfail)

        # Artifact Selection and Prioritization
        cs_sp = self.Cell(Tasks.CODE_SCOPE_SELECTION_PRIORITIZATION)
        cs_sp.set_status(task_status_map(Tasks.CODE_SCOPE_SELECTION_PRIORITIZATION))
        cc.add_dependency(cs_sp)

        t_sp = self.Cell(Tasks.TESTS_SELECTION_PRIORITIZATION)
        t_sp.set_status(task_status_map(Tasks.TESTS_SELECTION_PRIORITIZATION))
        passfail.add_dependency(t_sp)

        m_sp = self.Cell(Tasks.MUTANTS_SELECTION_PRIORITIZATION)
        m_sp.set_status(task_status_map(Tasks.MUTANTS_SELECTION_PRIORITIZATION))
        wm.add_dependency(m_sp)
        mc.add_dependency(m_sp)

        # Artifact Generation
        cs_gen = self.Cell(Tasks.CODE_SCOPE_GENERATION)
        cs_gen.set_status(task_status_map(Tasks.CODE_SCOPE_GENERATION))
        cs_sp.add_dependency(cs_gen)

        t_gen = self.Cell(Tasks.TESTS_GENERATION)
        t_gen.set_status(task_status_map(Tasks.TESTS_GENERATION))
        t_sp.add_dependency(t_gen)

        m_gen = self.Cell(Tasks.MUTANTS_GENERATION)
        m_gen.set_status(task_status_map(Tasks.MUTANTS_GENERATION))
        m_sp.add_dependency(m_gen)

        # Starting
        starting = self.Cell(Tasks.STARTING)
        starting.set_status(task_status_map(Tasks.STARTING))
        cs_gen.add_dependency(starting)
        t_gen.add_dependency(starting)
        m_gen.add_dependency(starting)

        # COMPUTE THE USES AND VERIFY
        visited = {}
        self._compute_uses_recursive(self.root, visited)

        ## Verify
        number_of_tasks = len(Tasks) # Number of instances in 'Tasks' class
        if len(visited) != number_of_tasks:
            logging.error("%s %s" % ("BUG in the Task Ordering Dependency.", \
                    "got %d but expects %d" % (len(visited), number_of_tasks)))
            ERROR_HANDLER.error_exit()
        visited = {}
        self._recursive_verify(self.root, visited)
    #~ def initialize_data_graph()

    def complete_task (self, task_name):
        # look the task up from the root
        t = self._lookup_task_cell(task_name)
        # Check that all deps are done
        self._recursive_check_deps_are_done(t)
        # set it to complete
        t.set_done()
    #~ def complete_task()

    def task_is_complete(self, task_name):
        t = self._lookup_task_cell(task_name)
        return t.is_done()
    #~ def task_is_complete()

    def task_is_executing(self, task_name):
        t = self._lookup_task_cell(task_name)
        return t.is_executing()
    #~ def task_is_executing()

    def task_is_untouched(self, task_name):
        t = self._lookup_task_cell(task_name)
        return t.is_untouched()
    #~ def task_is_untouched()

    def get_next_todo_tasks(self):
        task_node_set = set()
        self._recursive_get_next_todo_tasks(task_node_set, self.root)
        task_set = {x.get_task_name() for x in task_node_set}
        if len(task_set) != len(task_node_set):
            logging.error("%s" % (("BUG) same task appears in multiple nodes")))
            ERROR_HANDLER.error_exit()
        return task_set
    #~ def get_next_todo_tasks()

    def set_task_back_as_todo_untouched(self, task_name):
        t = self._lookup_task_cell(task_name)
        self._recursive_set_task_back_as_todo_untouched(t)  
    #~ def set_task_back_as_todo_untouched()

    # ==== PRIVATE ====

    class Cell():
        def __init__(self, task_name, status=Status.UNTOUCHED):
            self.dependencies = set()
            self.uses = set()
            self.status = status
            self.task_name = task_name
            if not Status.is_valid(self.status):
                logging.error("Invalid value passed as status, use 'Status.'")
                ERROR_HANDLER.error_exit_file(__file__)                

        # setters
        def add_dependency(self, cell):
            self.dependencies.add(cell)
        def add_use(self, cell):
            self.uses.add(cell)
        def set_status(self, status):
            if not Status.is_valid(status):
                logging.error( \
                    "Invalid status value passed in set_status.use 'Status.'")
                ERROR_HANDLER.error_exit_file(__file__)                
            self.status = status
        def set_done(self):
            self.status = Status.DONE
        def set_executing(self):
            self.status = Status.EXECUTING
        def set_untouched(self):
            self.status = Status.UNTOUCHED
        # getters
        def get_dependencies(self):
            return self.dependencies
        def get_uses(self):
            return self.uses
        def get_status(self):
            return self.status
        def get_task_name(self):
            return self.task_name
        # extra getters
        def is_done(self):
            return self.status == Status.DONE
        def is_executing(self):
            return self.status == Status.EXECUTING
        def is_untouched(self):
            return self.status == Status.UNTOUCHED
    #~ class Cell

    def _compute_uses_recursive(self, start_node, visited):
        '''
        Recursively set the use of the nodes (in the dependencies)
        Using DFS, just update the already visited deps, no recursive call

        :param start_node: currently explored node
        :param visited: list of visited nodes (already called recusively)
        '''
        if start_node not in visited:
            visited.add(start_node)
            for d in start_node.get_dependencies():
                d.add_use(start_node)
                self._compute_uses_recursive(d, visited)
    #~ def _compute_uses_recursive() 

    def _recursive_verify(self, start_node, visited):
        # verify no loop and status soundness
        if start_node in visited:
            logging.error("There is a loop involving task {}".format( \
                                    start_node.get_task_name().get_name()))
            ERROR_HANDLER.error_exit_file(__file__)
        for d in start_node.get_dependencies():
            if not start_node.is_untouched():
                if not d.is_done():
                    logging.error("{} {} {} {} {}".format( \
                                    "Unsoundness of status. dependency", \
                                    d.get_task_name().get_name(), \
                                    "not done while use", \
                                    start_node.get_task_name().get_name(), \
                                    "is either executing or done"))
                    ERROR_HANDLER.error_exit_file(__file__)
            self._recursive_verify(d, visited.copy())
    #~ def _recursive_verify()

    def _recursive_lookup(self, task_name, start_node):
        if start_node.task_name == task_name:
            return start_node
        for d_node in start_node.get_dependencies():
            ret = self._recursive_lookup(task_name, d_node)
            if ret is not None:
                return ret
        return None
    #~ def _recursive_lookup()

    def _lookup_task_cell(self, task_name):
        cell = self._recursive_lookup(task_name, self.root)
        if cell is None:
            logging.error("%s %s" % \
                ("The Task looked up does not exist in dep graph", task_name))
            ERROR_HANDLER.error_exit()
        return cell
    #~ def _lookup_task_cell()

    def _recursive_check_deps_are_done(self, start_node):
        problem = None
        for d in start_node.get_dependencies():
            if not d.is_done():
                problem = d.get_task_name
                break
            self._recursive_check_deps_are_done(d)
        if problem is not None:
            logging.error("%s %s %s %s" % ("task", start_node.get_task_name, \
                        "is done while the dependencies are not:", problem))
            ERROR_HANDLER.error_exit()
    #~ def _recursive_check_deps_are_done()

    def _recursive_set_task_back_as_todo_untouched(self, start_node):
        if not start_node.is_untouched():
            start_node.set_untouched()
            for u in start_node.get_uses():
                self._recursive_set_task_back_as_todo_untouched(u)
    #~ def _recursive_set_task_back_as_todo_untouched

    def _recursive_get_next_todo_tasks(self, task_set, start_node):
        if start_node.is_done():
            return
        is_leaf = True
        for d in start_node.get_dependencies():
            if not d.is_done():
                is_leaf = False
                self._recursive_get_next_todo_tasks(task_set, d)
        if is_leaf:
            task_set.add(start_node)
    #~ def _recursive_get_next_todo_tasks()
#~ class TaskOrderingDependency


