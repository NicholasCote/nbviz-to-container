# nbviz-to-container
A containerization example that takes a interactive visualization in a Jupyter notebook and turns it in to a containerized web server

## Prerequisites
In order to work through this example on your local machine make sure you have installed the following programs

* [Python](https://wiki.python.org/moin/BeginnersGuide/Download)
* [pip](https://pip.pypa.io/en/stable/installation/)
* [nbconvert](https://nbconvert.readthedocs.io/en/latest/install.html) included in [Jupyter Notebook](https://docs.jupyter.org/en/latest/install/notebook-classic.html) or [JupyterLab](https://jupyterlab.readthedocs.io/en/stable/getting_started/installation.html)
* [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
* [Mamba](https://github.com/conda-forge/miniforge#install)
* [Podman](https://podman.io/docs/installation) or [Docker](https://docs.docker.com/engine/install/)

## Notebook Example
Please use the walkthrough.ipynb file for an interactive example that takes an existing notebook and creates a web server running in a container to display an interactive visualization. 

### How to get started

Run the following in a terminal/command line. Use the Operating Systems search function to look for terminal if this is unfamiliar.  

`git clone https://github.com/NicholasCote/nbviz-to-container.git`

The best way to run the content is inside a Jupyter environment. Jupyter Lab is more robust than Notebook, but either can be used. Change the directory to be inside the git repository

`cd nbviz-to-container`

`jupyter lab walkthrough.ipynb`

This should start a Jupyter Lab session with the walkthrough notebook which can be used to ensure the perquisites that haven't been used yet are installed prior to starting the content. 

**Note:** If additional software is required after Jupyter Lab is started it may need to be restarted in a new terminal session to make sure it can use the newly installed applications. 