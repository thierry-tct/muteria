This is the entry point of the framework. It is structured as following:
- `main_controller.py` Implements the controller entry point to handle the 
  different execution modes. Then for each execution mode, it calls the 
  corresponding functionnality.
- `executor.py` Implement the executor orchestrator for the testing process:
    test criteria test objectives generation or instrumentation, test generation,
    test execution, reporting,...
