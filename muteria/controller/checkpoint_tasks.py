""" This Module implement the data structore and format for the 
    Checkpointing of the main controller during the execution phase

    The importants classes or elements are:
    - `Tasks` enum: enum that defines the differents tasks that are 
                    checkpointed during the controller execution.    
    - `Status` enum: enum defining the different states that a task can 
                    have (untouched, executing or done)
    - `TaskOrderingDependency` class: That defines the dependency between
                    the different tasks as well as their status.
                    The state changes as well as the task to run next are 
                    also implemented in the class.
"""


from __future__ import print_function

import logging
import collections

import networkx

import muteria.common.mix as common_mix

ERROR_HANDLER = common_mix.ErrorHandler


class Tasks(common_mix.EnumAutoName):
    STARTING = 0 #enum.auto()

    TESTS_GENERATION_GUIDANCE = 1 #enum.auto()
    TESTS_GENERATION = 2 #enum.auto()
    TESTS_GENERATION_USING_CRITERIA = 3 #enum.auto()
    TESTS_EXECUTION_SELECTION_PRIORITIZATION = 4 #enum.auto()
    PASS_FAIL_TESTS_EXECUTION = 5 #enum.auto()

    CRITERIA_GENERATION_GUIDANCE = 6 #enum.auto()
    CRITERIA_GENERATION = 7 #enum.auto()
    CRITERIA_EXECUTION_SELECTION_PRIORITIZATION = 8 #enum.auto()
    CRITERIA_TESTS_EXECUTION = 9 #enum.auto()

    PASS_FAIL_STATS = 10 #enum.auto()
    CRITERIA_STATS = 11 #enum.auto()
    AGGREGATED_STATS = 12 #enum.auto()

    FINISHED = 13 #enum.auto()
#~ class Tasks

class Status(common_mix.EnumAutoName):
    UNTOUCHED = -1 #enum.auto()
    EXECUTING = 0 #enum.auto()
    DONE = 1 #enum.auto()
#~ class Status

class TaskOrderingDependency(object): 
    '''
    The task dependency structure is following(The structure neve change):
    ----------------------------------------------------------------------
        TESTS_GENERATION_GUIDANCE --> STARTING
        CRITERIA_GENERATION_GUIDANCE --> STARTING

        TESTS_GENERATION --> TESTS_GENERATION_GUIDANCE

                                            | TESTS_GENERATION_GUIDANCE
        TESTS_GENERATION_USING_CRITERIA --> | CRITERIA_GENERATION 

                                                     | TESTS_GENERATION_USING_CRITERIA 
        TESTS_EXECUTION_SELECTION_PRIORITIZATION --> | TESTS_GENERATION

        PASS_FAIL_TESTS_EXECUTION --> TESTS_EXECUTION_SELECTION_PRIORITIZATION

        CRITERIA_GENERATION --> CRITERIA_GENERATION_GUIDANCE

        CRITERIA_EXECUTION_SELECTION_PRIORITIZATION --> CRITERIA_GENERATION 

                                     | CRITERIA_EXECUTION_SELECTION_PRIORITIZATION
        CRITERIA_TESTS_EXECUTION --> | PASS_FAIL_TESTS_EXECUTION

        PASS_FAIL_STATS --> PASS_FAIL_TESTS_EXECUTION

        CRITERIA_STATS --> CRITERIA_TESTS_EXECUTION

                             | PASS_FAIL_STATS
        AGGREGATED_STATS --> | CRITERIA_STATS

        FINISHED --> AGGREGATED_STATS
    ------------------------------------------------------------------------

    '''
    def __init__(self, json_obj=None):
        if json_obj is None:
            self.initialize_data_graph()
        else:
            # Check that every task is present
            if type(json_obj) != dict:
                ERROR_HANDLER.error_exit("{} {}".format(\
                        "Invalid object to initialize", \
                        "TaskOrderingDependency, must be a 'dict'"), __file__)
            if len(json_obj) != len(Tasks):
                ERROR_HANDLER.error_exit("{} {}".format(\
                            "Invalid object to initialize", \
                            "TaskOrderingDependency. Size mismatch"), __file__)
            # verify
            for key_t in Tasks:
                if key_t.get_str() not in json_obj:
                    ERROR_HANDLER.error_exit("{} {} {} {}".format( \
                        "Invalid object to initialize TaskOrderingDependency",\
                        "The task", key_t.get_str(), "is absent in json_obj"),\
                                                                    __file__)
                if not Status.has_element_named(json_obj[key_t.get_str()]):
                    ERROR_HANDLER.error_exit("{} {} {} {}".format( \
                        "Invalid object to initialize TaskOrderingDependency",\
                        "The task", key_t.get_str(), "has invalid status"), \
                                                                    __file__)
            # initialize
            decoded_json_obj = {}
            for k_str, v_str in json_obj.items():
                decoded_json_obj[Tasks[k_str]] = Status[v_str]
            self.initialize_data_graph(decoded_json_obj)
    #~ def __init__()

    def get_as_json_object(self):
        ret_obj = {}
        for key_t in Tasks:
            ret_obj[key_t.get_str()] = \
                        self._lookup_task_cell(key_t).get_status().get_str()
        return ret_obj
    #~ def get_as_json_object()

    def export_graph(self, graph_out_filename):
        graph = networkx.Graph()
        # add nodes
        for key_t in Tasks:
            graph.add_node(key_t.get_str())
        # add edges
        visited = set()
        queue = collections.deque()
        visited.add(self.root)
        queue.append(self.root)
        while queue:
            cur_node = queue.popleft()
            for d in cur_node.get_dependencies():
                graph.add_edge(d.get_task_name().get_str(), \
                                        cur_node.get_task_name().get_str())
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
        finished = self.Cell(Tasks.FINISHED)
        finished.set_status(task_status_map[Tasks.FINISHED])

        self.root = finished

        # Construct the rest of the dependence graph, starting at the root
        ## Stats Layer
        ### Aggregate stats
        agg_stats =  self.Cell(Tasks.AGGREGATED_STATS)
        agg_stats.set_status(task_status_map[Tasks.AGGREGATED_STATS]) 
        finished.add_dependency(agg_stats)

        ### Other stats
        passfail_stats = self.Cell(Tasks.PASS_FAIL_STATS)
        passfail_stats.set_status(task_status_map[Tasks.PASS_FAIL_STATS])
        agg_stats.add_dependency(passfail_stats)

        crit_stats = self.Cell(Tasks.CRITERIA_STATS)
        crit_stats.set_status(task_status_map[Tasks.CRITERIA_STATS])
        agg_stats.add_dependency(crit_stats)

        ## Matrices Layer
        crit = self.Cell(Tasks.CRITERIA_TESTS_EXECUTION)
        crit.set_status(task_status_map[Tasks.CRITERIA_TESTS_EXECUTION])
        crit_stats.add_dependency(crit)

        passfail = self.Cell(Tasks.PASS_FAIL_TESTS_EXECUTION)
        passfail.set_status(task_status_map[Tasks.PASS_FAIL_TESTS_EXECUTION])
        passfail_stats.add_dependency(passfail)
        crit.add_dependency(passfail)

        # Artifact Execution Selection and Prioritization
        ce_sp = self.Cell(Tasks.CRITERIA_EXECUTION_SELECTION_PRIORITIZATION)
        ce_sp.set_status(task_status_map[ \
                            Tasks.CRITERIA_EXECUTION_SELECTION_PRIORITIZATION])
        crit.add_dependency(ce_sp)

        t_sp = self.Cell(Tasks.TESTS_EXECUTION_SELECTION_PRIORITIZATION)
        t_sp.set_status(task_status_map[\
                            Tasks.TESTS_EXECUTION_SELECTION_PRIORITIZATION])
        passfail.add_dependency(t_sp)

        # Artifact Generation
        t_gen_crit = self.Cell(Tasks.TESTS_GENERATION_USING_CRITERIA)
        t_gen_crit.set_status(task_status_map[Tasks.TESTS_GENERATION_USING_CRITERIA])
        t_sp.add_dependency(t_gen_crit)

        crit_gen = self.Cell(Tasks.CRITERIA_GENERATION)
        crit_gen.set_status(task_status_map[Tasks.CRITERIA_GENERATION])
        ce_sp.add_dependency(crit_gen)
        t_gen_crit.add_dependency(crit_gen)

        t_gen = self.Cell(Tasks.TESTS_GENERATION)
        t_gen.set_status(task_status_map[Tasks.TESTS_GENERATION])
        t_sp.add_dependency(t_gen)

        t_gguide = self.Cell(Tasks.TESTS_GENERATION_GUIDANCE)
        t_gguide.set_status(task_status_map[Tasks.TESTS_GENERATION_GUIDANCE])
        t_gen.add_dependency(t_gguide)
        t_gen_crit.add_dependency(t_gguide)

        c_gguide = self.Cell(Tasks.CRITERIA_GENERATION_GUIDANCE)
        c_gguide.set_status(task_status_map[Tasks.CRITERIA_GENERATION_GUIDANCE])
        crit_gen.add_dependency(c_gguide)

        # Starting
        starting = self.Cell(Tasks.STARTING)
        starting.set_status(task_status_map[Tasks.STARTING])
        c_gguide.add_dependency(starting)
        t_gguide.add_dependency(starting)

        # COMPUTE THE USES AND VERIFY
        visited = set()
        self._compute_uses_recursive(self.root, visited)

        ## Verify
        number_of_tasks = len(Tasks) # Number of instances in 'Tasks' class
        if len(visited) != number_of_tasks:
            ERROR_HANDLER.error_exit("%s %s" % (\
                    "BUG in the Task Ordering Dependency. got", \
                    "%d but expects %d" % (len(visited), number_of_tasks)),\
                                                                    __file__)
        visited = {}
        self._recursive_verify(self.root, visited)
    #~ def initialize_data_graph()

    def set_task_completed (self, task_name):
        # look the task up from the root
        t = self._lookup_task_cell(task_name)
        # Check that all deps are done
        self._recursive_check_deps_are_done(t)
        # set it to complete
        t.set_done()
        logging.info("checkpoint_tasks:COMPLETED:"+task_name.get_str())
    #~ def set_task_completed()

    def set_task_executing (self, task_name):
        # look the task up from the root
        t = self._lookup_task_cell(task_name)
        # Check that all deps are done
        self._recursive_check_deps_are_done(t)
        # set it to complete
        t.set_executing()
        logging.info("checkpoint_tasks:EXECUTING:"+task_name.get_str())
    #~ def set_task_executing()

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
            ERROR_HANDLER.error_exit("{}".format(\
                        "(BUG) same task appears in multiple nodes"), __file__)
        logging.info("checkpoint_tasks:NEXT_TODO:"+\
                                        str([t.get_str() for t in task_set]))
        return task_set
    #~ def get_next_todo_tasks()

    def set_all_tasks_to_completed(self):
        task_name_set = self.get_next_todo_tasks()
        for task_name in task_name_set:
            t = self._lookup_task_cell(task_name)
            self._recursive_set_task_as_done(t)
    #~ def set_all_tasks_to_completed()

    def set_task_back_as_todo_executing(self, task_name):
        t = self._lookup_task_cell(task_name)
        if not t.is_executing():
            t.set_executing()
            for u in t.get_uses():
                self._recursive_set_task_back_as_todo_untouched(u)
    #~ def set_task_back_as_todo_executing()

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
                ERROR_HANDLER.error_exit(\
                            "Invalid value passed as status, use 'Status.'", \
                                                                    __file__)

        # setters
        def add_dependency(self, cell):
            self.dependencies.add(cell)
        def add_use(self, cell):
            self.uses.add(cell)
        def set_status(self, status):
            if not Status.is_valid(status):
                ERROR_HANDLER.error_exit( \
                    "Invalid status value passed in set_status.use 'Status.'",\
                                                                    __file__)
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
        :param visited: set of visited nodes (already called recusively)
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
            ERROR_HANDLER.error_exit(\
                            "There is a loop involving task {}".format( \
                            start_node.get_task_name().get_str()), __file__)
        for d in start_node.get_dependencies():
            if not start_node.is_untouched():
                if not d.is_done():
                    ERROR_HANDLER.error_exit("{} {} {} {} {}".format( \
                                    "Unsoundness of status. dependency", \
                                    d.get_task_name().get_str(), \
                                    "not done while use", \
                                    start_node.get_task_name().get_str(), \
                                    "is either executing or done"), __file__)
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
            ERROR_HANDLER.error_exit("%s %s" % \
                ("The Task looked up does not exist in dep graph", task_name),\
                                                                    __file__)
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
            ERROR_HANDLER.error_exit("%s %s %s %s" % (\
                        "task", start_node.get_task_name, \
                        "is done while the dependencies are not:", problem),\
                                                                    __file__)
    #~ def _recursive_check_deps_are_done()

    def _recursive_set_task_as_done(self, start_node):
        if not start_node.is_done():
            start_node.set_done()
            for u in start_node.get_uses():
                self._recursive_set_task_as_done(u)
    #~ def _recursive_set_task_as_done()

    def _recursive_set_task_back_as_todo_executing(self, start_node):
        if not start_node.is_executing():
            start_node.set_executing()
            for u in start_node.get_uses():
                self._recursive_set_task_back_as_todo_executing(u)
    #~ def _recursive_set_task_back_as_todo_executing()

    def _recursive_set_task_back_as_todo_untouched(self, start_node):
        if not start_node.is_untouched():
            start_node.set_untouched()
            for u in start_node.get_uses():
                self._recursive_set_task_back_as_todo_untouched(u)
    #~ def _recursive_set_task_back_as_todo_untouched()

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


