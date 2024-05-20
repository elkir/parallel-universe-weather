# Parallel Computing for Parallel Universe Weather

## Overview


The computation framework has been developed to allow efficient distributed computing necessary to work with the ECMWF ENSemble Weather Forecast datsets.

It is an OOP platform designed to automate and manage large-scale distributed computations at the Cambridge High-Performance Computing (HPC) environment as well as at local systems. This framework leverages Apache Airflow for workflow orchestration and SLURM for job scheduling.

## Problem Statement

Managing complex workflows, data handling, and resource optimization in HPC environments is challenging. This framework addresses these issues by automating tasks, optimizing resource allocation, and providing a flexible experimentation environment.

## Key Features

- **Workflow Automation**: Uses Apache Airflow to define and manage Directed Acyclic Graphs (DAGs) for complex computational workflows.
- **HPC Integration**: Utilizes SLURM for efficient job scheduling and resource management.
- **Scalable Data Management**: Automates data transfer and storage management for large datasets, between different types of storage setups.
- **Flexible Experimentation**: Facilitates seamless transition from Jupyter Notebooks to production scripts.

## Installation


1. **Set up the Conda environment**:
    ```bash
    conda env create -f environment.yml
    conda activate parallel_universe_weather
    ```



## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For more information, look at resources at the [ENS Dataset project webpage](https://www.cl.cam.ac.uk/~pd423) 

---

