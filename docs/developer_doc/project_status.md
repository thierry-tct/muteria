# Project Status

## Current Limitation
- Interface difference between multiple versions of the same tool 

---
## Development
### Things to fix
- Ensure tools plugins do not leave the repo srcs or exes in an infected state. They must cleanup the changes made. Ensure that by cleaning for them at top level (when the driver's methods are called in the meta tools)
- Handle reporting test error in stats (first within meta test execution)
- Enable having no criterion set

- Complete and test the web UI.
- Choice of test level (unit, system, ...)
- Complete the documentation
- Augment the test suite

### Features 
1. parallelism
- [ ] Implement option to run phases of the analysis in parallel.
- [ ] Implement option to run tests in parallel 
2. Web Interface
- [x] Front-end UI
- [x] server (back-end)
- [ ] Write custom configuration function on-line
- [ ] Write manual tests on-line
3. Command Line Interface
- [x] basic interaction to launch execution
1. Library API interface
- [x] API in docstring 
- [ ] make the documented API available
5. Reporting
- [x] Basic metric display
- [ ] cross project reporting (for experiment and evolution)
- [ ] plotting
6. Checkpointing and Logging
- [x] checkpoint and logging implemented
- [x] logging optional
- [ ] checkpointing optional
7. Multiple projects
- [ ] obtain data from previous versions execution in current (regression)
- [ ] merge data across multiple project (for experiments)
8. Test Adequacy Criteria(TAC)
- [x] Support adding new TACs
- [x] Support enabling/disabling TAC during execution 
9. Tools
- [x] support plugging in test generation tools
- [x] support plugging in TAC instrumenting tools
- [ ] support plugging in TAC test objectives selection/prioritization.
- [ ] support plugging in test case selection prioritization techniques.
- [x] support adding test formats (for test execution)
- [ ] support adding build systems.

