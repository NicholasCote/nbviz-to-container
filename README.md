# nbviz-to-container
A containerization example that takes a interactive visualization in a Jupyter notebook and turns it in to a containerized web server

## Workshops
Hybrid workshops were held to go over the content contained in this repository. 

The first workshop was held on June 20th, 2024. To watch a recording of that workshop, see [Tutorial: From Jupyter Notebook to Web Server: Containerizing Interactive Visualizations](https://youtu.be/Bhj2KdZcK70). The content covered during that workshop is captured in the walkthrough.ipynb file in the June-20-2024 directory in this repository. 

A second workshop is going to be held on August 8th, 2024. For additional details on that workshop, see [From Jupyter Notebook to Web Server: Automating Container Deployments with GitHub Actions](https://www.cisl.ucar.edu/events/jupyter-notebook-web-server-automating-container-deployments-github-actions).The content that will be covered during that workshop is captured in the walkthrough.ipynb file in the August-08-2024 directory in this repository. 

## Prerequisites
**Note:** If Docker is already installed there is a container image available that contains everything else

In order to work through this example on your local machine make sure you have installed the following programs:

* [Python](https://wiki.python.org/moin/BeginnersGuide/Download)
* [pip](https://pip.pypa.io/en/stable/installation/)
* [Jupyter Notebook](https://docs.jupyter.org/en/latest/install/notebook-classic.html) or [JupyterLab](https://jupyterlab.readthedocs.io/en/stable/getting_started/installation.html)
* [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
* [Mamba](https://github.com/conda-forge/miniforge#install)
* [Podman](https://podman.io/docs/installation) or [Docker](https://docs.docker.com/engine/install/)

## Notebook Example
### Creating an interactive visualization in a container
For an interactive example that takes an existing notebook and creates a web server running in a container to display an interactive visualization, see the walkthrough.ipynb file located in the June-20-2024 directory. 

### Automating container builds and deployments
For an interactive example that takes a container image file and automates building an image from it while updating an actual deployment configuration to use the new image, see the walkthrough.ipynb file located in the August-08-2024 directory. 

### How to get started

**Note:** There is a section on creating a [GitHub Action](https://docs.github.com/en/actions) to build the container and push it to Docker Hub. This requires a [GitHub account](https://github.com/signup?ref_cta=Sign+up&ref_loc=header+logged+out&ref_page=%2F&source=header-home), a [Docker Hub account](https://hub.docker.com/signup), and for the example repository to be [forked](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo). 

#### Via Docker

There is a container image available that contains all the prerequisites. Please note it is run via Docker, but only Podman is available to build inside the container. 

`docker run --privileged -p 8888:8888 docker.io/ncote/podman-notebook:2024-06-20 jupyter lab --ip 0.0.0.0`

When it starts there will be a link displayed that starts with **http://127.0.0.1:8888/lab?token=**. This link must be used to launch the application as it contains a required security token. Once inside the Jupyter Lab session this repository, or a forked version, needs to be cloned. This can be done via the Terminal included in Jupyter Lab or via an extension. More information on how to use the Git extension can be found at this [link to jupyterlab-git GitHub](https://github.com/jupyterlab/jupyterlab-git#jupyterlab-git). Once the repository contents have been added open the nbviz-to-container directory and the walkthrough.ipynb to follow the rest of the content. 

#### Via personal computer

Run the following in a terminal/command line. Use the Operating Systems search function to look for terminal if this is unfamiliar.  

`git clone https://github.com/NicholasCote/nbviz-to-container.git`

The best way to run the content is inside a Jupyter environment. Jupyter Lab is more robust than Notebook, but either can be used. Change the directory to be inside the git repository

`cd nbviz-to-container`

`jupyter lab walkthrough.ipynb`

This should start a Jupyter Lab session with the walkthrough notebook which can be used to ensure the perquisites that haven't been used yet are installed prior to starting the content. 

**Note:** If additional software is required after Jupyter Lab is started it may need to be restarted in a new terminal session to make sure it can use the newly installed applications. 