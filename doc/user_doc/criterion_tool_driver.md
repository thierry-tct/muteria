# Writing drivers for test criteria tools

The following steps must be followed to implement a new driver. The final driver may be pushed to the [muteria](https://github.com/muteria/muteria)'s github repository, to be used by others.

1. The driver's code must be located in the folder `muteria/drivers/criteria/tools_by_languages/<Language>/<Driver-Folder>`.

2. An `__init__.py` file must be created in the driver folder (`<Driver-Folder>`) and assign the driver's class name to `StaticCriteriaTool` as following: `StaticCriteriaTool = <Driver-Class>`. See for example the case of [Mart](https://github.com/thierry-tct/mart)'s driver in `muteria/drivers/criteria/tools_by_languages/c/mart/__init__.py`

3. The driver's class must extend the class `BaseCriteriaTool`, located in `muteria/drivers/criteria/base_testcriteriatool.py`, and implement all the _abstract_ methods (see for example [Mart](https://github.com/thierry-tct/mart)'s driver in `muteria/drivers/criteria/tools_by_languages/c/mart/mart.py`). The abstract methods that must be implemented are listed bellow.

---

``` Python
    @classmethod
    def installed(cls, custom_binary_dir=None)
```
This method checks whether the tool is installed. It returns a boolean representing whether the tool is installed (executable is accessible on the path) or not. `True` means that the tool is installed, else `False` is returned.

| Paramter | Type | Description |
|--|--|--|
| `custom_binary_dir` | `string` | custom directory to look for the relevant executable files for the corresponding tool. None means that the file are on the _PATH_. |

---

``` Python
    @classmethod
    def _get_meta_instrumentation_criteria(cls)
```
This method returns the list of test criteria whose elements are instrumented in the same file. An example is `[TestCriteria.STATEMENT_COVERAGE, TestCriteria.BRANCH_COVERAGE, TestCriteria.FUNCTION_COVERAGE]` from `GCov`. The various test criteria are defined in the class `TestCriteria` of the file `muteria/drivers/criteria/__init__.py`. 
_Note_: New defined criteria can be added in that class.

---

``` Python
    @classmethod
    def _get_separated_instrumentation_criteria(cls)
```
This method returns the list of test criteria whose elements are instrumented in different files (such as mutation). An example is `[TestCriteria.STRONG_MUTATION]` from `Mart`. The various test criteria are defined in the class `TestCriteria` of the file `muteria/drivers/criteria/__init__.py`. 
_Note_: New defined criteria can be added in that class.

---

``` Python
    def get_instrumented_executable_paths_map(self, enabled_criteria)
```
This method takes a list of test criteria and returns, for each criterion, the path to the corresponding instrumented executable file. The returned value is a `dict` which has criteria as keys and corresponding executables as values.

| Paramter | Type | Description |
|--|--|--|
| `enabled_criteria` | `list` | list of test criteria for which the instrumented executable file should be obtained. |

---

``` Python
    def get_criterion_info_object(self, criterion)
```
This method takes a test criterion and returns its corresponding info object. The info onject contains information about the element considered for the criterion (example mutants for mutation tool, statement for statement coverage tool). The info object for criterion is an object of the class `CriterionElementInfoObject`, defined in the file `muteria/drivers/criteria/criteria_info.py`

| Paramter | Type | Description |
|--|--|--|
| `criterion` | `TestCriteria.<criterion>` | test criterion of interet. |

---

``` Python
    def _get_criterion_element_executable_path(self, criterion, element_id):
```
This method takes a test criterion and an element ID and returns its execuable path map. An executable path map is a dict whose keys are executable relative path within the project repository, and the values are the element executable file path.

| Paramter | Type | Description |
|--|--|--|
| `criterion` | `TestCriteria.<criterion>` | test criterion of interet. |
| `element_id` | `string` | ID of the element of interest for the criterion of interest. |

---

``` Python
    def _get_criterion_element_environment_vars(self, criterion, element_id)
```
This method takes a test criterion and an element ID and returns its execution environment variable dict. An environment variable dict is a dict whose keys are environmet variables and values are their values. This is particularly useful in contexts such as mutant schemata, when the ID of the mutant to execute should be given as evironment variable at runtime (This function would return something like `{"MUTANT_ID": 1}`).

| Paramter | Type | Description |
|--|--|--|
| `criterion` | `TestCriteria.<criterion>` | test criterion of interet. |
| `element_id` | `string` | ID of the element of interest for the criterion of interest. |

---

``` Python
    def _get_criteria_environment_vars(self, result_dir_tmp, enabled_criteria)
```
This method takes a temporary dir and a list of test criteria and returns the envirnment variables to pass to the instrumented program at runtime. This is passed when executing criteria that do not have separated files, such as weak mutation, statement coverage, ...

| Paramter | Type | Description |
|--|--|--|
| `result_dir_tmp` | `string` | temporary dir where some files specified in env vars can be stored. Example of log files to record weak mutation results. |
| `enabled_criteria` | `list` | list of test criteria for which the env vars should be obtained. |

---

``` Python
    def _collect_temporary_coverage_data(self, criteria_name_list, \
                                            test_execution_verdict, \
                                            used_environment_vars, \
                                            result_dir_tmp, \
                                            testcase)
```
This method takes a list of test criteria names, test execution verdics, env vars used during test execution and temporary folder (same as function `_get_criteria_environment_vars`) and a list of test criteria, and the test case executed. It then processes the data comming from the execution (such as converting the `.gcda` files to `.gcov` files in GCov. See `muteria/drivers/criteria/tools_by_languages/c/gcov/gcov.py`)

| Paramter | Type | Description |
|--|--|--|
| `criteria_name_list` | `list` | list of test criteria of interest. |
| `test_execution_verdict` | `tuple` | Test execution verdict pair, made a boolean recording whether the test passed of failed, and the output log of the test execution. |
| `used_environment_vars` | `dict` | environment vars used when executing the test on the instrumented code. useful to find back where the recorded log was stored for example. |
| `result_dir_tmp` | `string` | temporary dir where temporary file from execution were saved. Example of log files to record weak mutation results. |
| `testcase` | `string` | Name of the testcase that was executed, and for which the coverage is being collected. |

---

``` Python
    def _extract_coverage_data_of_a_test(self, enabled_criteria, \
                                    test_execution_verdict, result_dir_tmp)
```
This method takes a list of test criteria, test execution verdics, temporary dir (same as function `_get_criteria_environment_vars`), then read use the data computed in `_collect_temporary_coverage_data` to compute the actual coverages. See `muteria/drivers/criteria/tools_by_languages/c/gcov/gcov.py`)

| Paramter | Type | Description |
|--|--|--|
| `enabled_criteria` | `list` | list of test criteria of interest. |
| `test_execution_verdict` | `tuple` | Test execution verdict pair, made a boolean recording whether the test passed of failed, and the output log of the test execution. |
| `result_dir_tmp` | `string` | temporary dir where temporary file from execution were saved. Example of log files to record weak mutation results. |

---

``` Python
    def _do_instrument_code (self, exe_path_map, code_builds_factory, \
                                        enabled_criteria, parallel_count=1)
```
This method instruments the code and stores the instrumented file according to `exe_path_map` (the instrumented file for the repository relative file `x/y/z` will be store into `exe_path_map["x/y/z"]`). For reference, see `muteria/drivers/criteria/tools_by_languages/c/gcov/gcov.py`)

| Paramter | Type | Description |
|--|--|--|
| `exe_path_map` | `dict` | map each repository file to the corresponding instrumented file intended location. |
| `code_builds_factory` | `CodeBuildsFactory` | Class that defines methods to handle repository tasks, such as building code, ... (see file `muteria/repositoryandcode/code_builds_factory.py`). |
| `enabled_criteria` | `list` | list of test criteria of interest. |
| `parallel_count` | `int` | number of threads or processes that are allowed to be used, in parallel, while intrumenting the code (for faster instrumentation). |

---
