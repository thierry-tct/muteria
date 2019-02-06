import logging
import enum


# TODO Find way to make the classes so that new elements cannot be added on the fly

@enum.unique
class Tasks(enum.Enum):
    STARTING = "STARTING"

    TESTS_GENERATION = "TESTS_GENERATION"
    TESTS_SELECTION_PRIORITIZATION = "TESTS_SELECTION_PRIORITIZATION"
    PASS_FAIL_TESTS_EXECUTION = "PASS_FAIL_TESTS_EXECUTION"

    CODE_SCOPE_GENERATION = "CODE_SCOPE_GENERATION"
    CODE_SCOPE_SELECTION_PRIORITIZATION = "CODE_SCOPE_SELECTION_PRIORITIZATION"
    CODE_COVERAGE_TESTS_EXECUTION = "CODE_COVERAGE_TESTS_EXECUTION"

    MUTANTS_GENERATION = "MUTANTS_GENERATION"

    MUTANTS_SELECTION_PRIORITIZATION = "MUTANTS_SELECTION_PRIORITIZATION"

    MUTANT_COVERAGE_TESTS_EXECUTION = "MUTANT_COVERAGE_TESTS_EXECUTION"
    WEAK_MUTATION_TESTS_EXECUTION = "WEAK_MUTATION_TESTS_EXECUTION"
    STRONG_MUTATION_TESTS_EXECUTION = "STRONG_MUTATION_TESTS_EXECUTION"

    PASS_FAIL_STATS = "PASS_FAIL_STATS"
    CODE_COVERAGE_STATS = "CODE_COVERAGE_STATS"
    MUTANT_COVERAGE_STATS = "MUTANT_COVERAGE_STATS"
    WEAK_MUTATION_STATS = "WEAK_MUTATION_STATS"
    STRONG_MUTATION_STATS = "STRONG_MUTATION_STATS"
    AGGREGATED_STATS = "AGGREGATED_STATS"

    FINISHING = "FINISHING"
#~ class Tasks

@enum.unique
class Status(enum.Enum):
    UNTOUCHED = -1
    EXECUTING = 0
    DONE = 1
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
    
    Each done_... param decide whether the corresponding task is already done

    '''
    def __init__(self, done_starting=False,
                        done_code_scope_generation=False,
                        done_test_generation=False,
                        done_mutant_generation=False,
                        done_code_scope_selection_prioritization=False,
                        done_tests_selection_prioritization=False,
                        done_mutant_selection_prioritization=False,
                        done_test_passfail_execution=False,
                        done_code_coverage_execution=False,
                        done_mutant_coverage_execution=False,
                        done_weak_mutant_execution=False,
                        done_strong_mutant_execution=False,
                        done_passfail_stats=False,
                        done_code_coverage_stats=False,
                        done_mutant_coverage_stats=False,
                        done_weak_mutation_stats=False,
                        done_strong_mutation_stats=False,
                        done_aggregated_stats=False,
                        done_finishing=False):
        # set the root cell (The root has no uses)
        finishing = Cell(Task.FINISHING)
        finishing.set_status(done_finishing)

        self.root = finishing

        # Construct the rest of the dependence graph, starting at the root
        ## Stats Layer
        ### Aggregate stats
        agg_stats =  Cell(Task.AGGREGATED_STATS)
        agg_stats.set_status(done_aggregated_stats)        
        finishing.add_dependency(agg_stats)

        ### Other stats
        passfail_stats = Cell(Task.PASS_FAIL_STATS)
        passfail_stats.set_status(done_passfail_stats)
        agg_stats.add_dependency(passfail_stats)

        cc_stats = Cell(Task.CODE_COVERAGE_STATS)
        cc_stats.set_status(done_code_coverage_stats)
        agg_stats.add_dependency(cc_stats)

        mc_stats = Cell(Task.MUTANT_COVERAGE_STATS)
        mc_stats.set_status(done_mutant_coverage_stats)
        agg_stats.add_dependency(mc_stats)

        wm_stats = cell(Task.WEAK_MUTATION_STATS)
        wm_stats.set_status(done_weak_mutation_stats)
        agg_stats.add_dependency(wm_stats)

        sm_stats = Cell(Task.STRONG_MUTATION_STATS)
        sm_stats.set_status(done_strong_mutation_stats)
        agg_stats.add_dependency(sm_stats)

        ## Matrices Layer
        sm = Cell(Task.STRONG_MUTATION_TESTS_EXECUTION)
        sm.set_status(done_strong_mutant_execution)
        sm_stats.add_dependency(sm)

        cc = Cell(Task.CODE_COVERAGE_TESTS_EXECUTION)
        cc.set_status(done_code_coverage_execution)
        cc_stats.add_dependency(cc)
        sm.add_dependency(cc)

        mc = Cell(Task.MUTANT_COVERAGE_TESTS_EXECUTION)
        mc.set_status(done_mutant_coverage_execution)
        mc_stats.add_dependency(mc)
        sm.add_dependency(mc)

        wm = Cell(Task.WEAK_MUTATION_TESTS_EXECUTION)
        wm.set_status(done_weak_mutant_execution)
        wm_stats.add_dependency(wm)
        sm.add_dependency(wm)

        passfail = Cell(Task.PASS_FAIL_TESTS_EXECUTION)
        passfail.set_status(done_test_passfail_execution)
        passfail_stats.add_dependency(passfail)
        cc.add_dependency(passfail)
        mc.add_dependency(passfail)
        wm.add_dependency(passfail)

        # Artifact Selection and Prioritization
        cs_sp = Cell(Task.CODE_SCOPE_SELECTION_PRIORITIZATION)
        cs_sp.set_status(done_code_scope_selection_prioritization)
        cc.add_dependency(cs_sp)

        t_sp = Cell(Task.TESTS_SELECTION_PRIORITIZATION)
        t_sp.set_status(done_tests_selection_prioritization)
        passfail.add_dependency(t_sp)

        m_sp = Cell(Task.MUTANTS_SELECTION_PRIORITIZATION)
        m_sp.set_status(done_mutant_selection_prioritization)
        wm.add_dependency(m_sp)
        mc.add_dependency(m_sp)

        # Artifact Generation
        cs_gen = Cell(Task.CODE_SCOPE_GENERATION)
        cs_gen.set_status(done_code_scope_generation)
        cs_sp.add_dependency(cs_gen)

        t_gen = Cell(Task.TESTS_GENERATION)
        t_gen.set_status(done_test_generation)
        t_sp.add_dependency(t_gen)

        m_gen = Cell(Task.MUTANTS_GENERATION)
        m_gen.set_status(done_mutant_generation)
        m_sp.add_dependency(m_gen)

        # Starting
        starting = Cell(STARTING)
        starting.set_status(done_starting)
        cs_gen.add_dependency(starting)
        t_gen.add_dependency(starting)
        m_gen.add_dependency(starting)

        # COMPUTE THE USES AND VERIFY
        visited = {}
        self._compute_uses_recursive(self.root, visited)

        ## Verify
        number_of_tasks = 19 # Number of instances in 'Task' class
        if len(visited) != number_of_tasks:
            logging.error("%s %s" % ("BUG in the Task Ordering Dependency.", \
                    "got %d but expects %d" % (len(visied), number_of_tasks))
            error_handler.error_exit()
    #~ def __init__()

    def complete_task (self, task_name):
        # look the task up from the root
        t = self._lookup_task_cell(task_name)
        # Check that all deps are done
        self._recursive_check_deps_are_done(t)
        # set it to complete
        t.set_status(True)
    #~ def complete_task()

    def task_is_complete(self, task_name):
        t = self._lookup_task_cell(task_name)
        return t.is_done()
    #~ def task_is_complete()

    def task_is_executing(self, task_name):
        t = self._lookup_task_cell(task_name)
        return t.is_executing()
    #~ def task_is_executing()

    def get_next_todo_tasks(self):
        task_node_set = set()
        self._recursive_get_next_todo_tasks(task_node_set, self.root)
        task_set = {x.get_task_name() for x in task_node_set}
        if len(task_set) != len(task_node_set):
            logging.error("%s" % (("BUG) same task appears in multiple nodes"))
            error_handler.error_exit()
        return task_set
    #~ def get_next_todo_tasks()

    def set_task_back_as_todo(self, task_name, set_untouch=True):
        t = self._lookup_task_cell(task_name)
        self._recursive_set_task_back_as_todo(t, set_untouch=set_untouched)  # TODO TODO: Also chanck the use of all functions in Cell
    #~ def set_task_back_as_todo()

    # ==== PRIVATE ====

    class Cell():
        def __init__(self, task_name, status=UNTOUCH):
            self.dependencies = set()
            self.uses = set()
            self.status = status
            self.task_name = task_name

        # setters
        def add_dependency(self, cell):
            self.dependencies.add(cell)
        def add_use(self, cell):
            self.uses.add(cell)
        def set_status(self, status):
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
                _compute_uses_recursive(d, visited)
    #~ def _compute_uses_recursive() 

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
        cell = self._recursive_lookup(self.root)
        if cell in None:
            logging.error("%s %s" % \
                ("The Task looked up does not exist in dep graph", task_name))
            error_handler.error_exit()
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
                        "is done while the dependencies are not:", problem)
            error_handler.error_exit()
    #~ def _recursive_check_deps_are_done()

    def _recursive_set_task_back_as_todo(self, start_node):
        if not start_node.is_untouched():
            start_node.set_status(False)
            for u in start_node.get_uses():
                self._recursive_set_task_back_as_todo(u)
    #~ def _recursive_set_task_back_as_todo

    def _recursive_get_next_todo_tasks(task_set, start_node):
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


