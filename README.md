# MUTERIA (MUlti-Tools and critERIA framework for automated software testing)
[https://github.com/muteria](https://github.com/muteria)

## Installation
1. Install the requirement by running: 
```
pip install -r requirements.txt
```
For developer, also install the developer requirements as following:
```
pip install -r developer-requirements.txt
```

---
## Development
### Things to fix
- [ ] MAKE SURE checkpoint restart and destroy affects the children
- [ ] Check checkpoint consistency everywhere & later add no checkpoint option
- [ ] Fix Test case info
- [ ] make mutant info
- [ ] codecoverage info
- [ ] supported testcase formats for testcase
- [ ] supported testgen executable format
- [ ] supported test execution executable format
- [ ] supported test level (unit, system, ...)
- [ ] configs must support comparison as following:
  ```python
  def __eq__(self, other):
      self.__dict__ == other.__dict__
  ```
### Features 
1. parallelism
- [ ] Implement option to run mutant coverage and weak mutation simultaneously
2. Web Interface and Server
- [ ]
3. Command Line Interface
- [ ]
4. Library API interface
-[ ]
5. Reporting
- [ ]
6. Checkpointing and Logging
- [ ]
7. Multiple projects
- [ ] 
  
