# DRIVERS
## TESTCASE_TOOL
1. BASE_TESTCASE_TOOL interesting methods
```python
__init__(work_dir, code_build_factory, tests_tool_config, checkpointer)

generate_tests()
runtests()
execute_testcase()
```
## META_TESTCASE_TOOL
1. \_\_init\_\_(language, work_dir, code_build_factory, tests_tool_config_list)
2. generate_tests()
3. runtests()
4. execute_testcase()

---
## CODE_COVERAGE_TOOL
1. \_\_init\_\_()
2. compute_coverage()

## META_CODE_COVERAGE_TOOL
1. \_\_init\_\_()
2. compute_coverage()

---
## MUTATION_TOOL
1. \_\_init\_\_()
2. generate_mutants()
3. runtests_mutant_coverage()
4. runtests_weak_mutation()
5. runtests_strong_mutation()

## META_MUTATION_TOOL
1. \_\_init\_\_()
2. generate_mutants()
3. runtests_mutant_coverage()
4. runtests_weak_mutation()
5. runtests_strong_mutation()

---
## TEST_CASE_EXECUTION_OPTIMIZER_TOOL
1. \_\_init\_\_()
2. re_initialize_data()
3. get_all_remaining_data()
4. get_next_data()
5. get_post_single_execution_callback()
6. select_elements()

## META_TEST_CASE_EXECUTION_OPTIMIZER_TOOL
1. \_\_init\_\_()
2. re_initialize_data()
3. get_all_remaining_data()
4. get_next_data()
5. get_post_single_execution_callback()
6. select_elements()

---
## TEST_GENERATION_GUIDANCE_TOOL
1. \_\_init\_\_()
2. get_ordered_guidance_elements()

## META_TEST_GENERATION_GUIDANCE_TOOL
1. \_\_init\_\_()
2. get_ordered_guidance_elements()

---
## MUTANT_EXECUTION_OPTIMIZER_TOOL
1. \_\_init\_\_()
2. re_initialize_data()
3. get_all_remaining_data()
4. get_next_data()
5. get_post_single_execution_callback()
6. select_elements()

## META_MUTANT_EXECUTION_OPTIMIZER_TOOL
1. \_\_init\_\_()
2. re_initialize_data()
3. get_all_remaining_data()
4. get_next_data()
5. get_post_single_execution_callback()
6. select_elements()

---

## Tool Config Class methods:
```python
1. get_tool_name()
# compute alias by using <toolname>.<configID>, when configID is not None.
2. get_tool_config_alias()  
3. get_tool_type()
```

---
---
## TODO Next:
1. Implement BaseTestcaseTool
2. Finalize TescaseInfo, must separate simple and meta
3. refactor Checkpoint handler name (common name)
4. Make squeletton for all other components (classed and interfaces). so as to just fill in later
5. Implement testcasetool config and BaseToolConfig
6. reorganize the classes to have them finalized. Also create dirs and source files for test prioritization...
7. Continue with main executor controller, code factory, repo manager, config manager, navigator,...