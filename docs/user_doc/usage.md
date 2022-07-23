# User Manual

## Suported Systems
*Muteria* is written in Python and thus can run on Windows, Linux or macOS.

## Installation
muteria requires Python 3.

1. Install Muteria by running: 
``` bash
pip install muteria
```

2. View the usage help:
```bash
muteria --help
```


## Usage
*Muteria* requires to have the underlying tools installed on the system.
### Usage example C (in Docker container)
A docker image, with preinstalled tools, can be used to run muteria on a sample C language program.
The installed tools are: [GNU GCov](https://gcc.gnu.org/onlinedocs/gcc/Gcov.html), [KLEE](https://klee.github.io/), [Shadow](https://srg.doc.ic.ac.uk/projects/shadow/shadow.html), [Mart](https://github.com/thierry-tct/mart), [SEMu](https://github.com/thierry-tct/KLEE-SEMu).

1. Pull the docker image:
``` bash
docker pull thierrytct/cm
```
2. run the docker image in a container:
``` bash
docker run -it --rm thierrytct/cm bash
```

3. Download the example program:
```bash
git clone https://github.com/muteria/example_c.git 
```

3. Change into the example program directory:
```bash
cd example_c
```
4. run using the configuration file in ctrl/conf.py
```bash
muteria --config ctrl/conf.py --lang c run
```

### Usage example Python

Example of measuring coverage for a python program using [coverage.py](https://coverage.readthedocs.io/).
1. Install `coverage.py`:
