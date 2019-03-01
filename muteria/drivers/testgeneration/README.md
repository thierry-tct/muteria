# Test Case Generation Package

This Module contains the implementation of the tests cases manager (test geneation and execution).

## Package Modules
1. **`MetaTestcaseTool`** Which is the high level test case tool that will controle underlying testcase tools.
   
   _```Note```_: This module is complete and a tool driver implementation need not to change it.
2. **`BaseTestcaseTool`** which is the abstract class to be extendend by each mutation tool's driver. 

    _```Note```_: Only the abstract methods must be overloaded. The others are optional.

### MetaTestcaseTool Module
This module presents methods related to test cases. 

**TODO**: Ensure that only one instance is existing at the same time for a specific working directory (use a global variable to count the instances created and report bug if more than 1 is created at the same time)

### BaseTestcaseTool Module
This is the base for each testcase tool's driver. The test case tools are divided into 2 categories:
-   Static testcase tools: Only requires the program under test to run.
-   Dynamic testcase tools: Can use existing testcases, coverage information, etc, in order to generate new tests.

When a tool is extending the `BaseTestcaseTool`, two variants can be defined: The static and the Dynamic. 
The only thing to ensure is to place make the Static and Dynamic testcase tools visible by Importing respectively as `StaticTestcaseTool` and `DynamicTestcaseTool`.

*`Note`*: Set `StaticTestcaseTool` or  `DynamicTestcaseTool` to `None` if either is not existing.

__USAGE EXAMPLES__

a)  Neither of Static or Dynamic tools are implemented, The `__init__.py` of the the tool package will be:
```python
StaticTestcaseTool = None
DynamicTestcaseTool = None
```
b)  Static tool is implemented as class _MyStaticTestcaseTool_ and Dynamic tool in class _MyDynamicTestcaseTool_, both in the source file `mytestcasetool.py`. The `__init__.py` of the the tool package will be:
```python
from mytestcasetool import MyStaticTestcaseTool as StaticTestcaseTool
from mytestcasetool import MyDynamicTestcaseTool as DynamicTestcaseTool
```
c)  Static tool is implemented as class _MyStaticTestcaseTool_ of the source file `mytestcasetool.py`, and Dynamic tool is not implemented. The `__init__.py` of the the tool package will be:
```python
from mytestcasetool import MyStaticTestcaseTool as StaticTestcaseTool
DynamicTestcaseTool = None
```
d)  Static tool is not implemented, and Dynamic tool is as class _MyDynamicTestcaseTool_ of the source file `mytestcasetool.py`. The `__init__.py` of the the tool package will be:
```python
StaticTestcaseTool = None
from mytestcasetool import MyDynamicTestcaseTool as DynamicTestcaseTool
```