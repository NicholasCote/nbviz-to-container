# Use an official Mamba image as the base image
FROM docker.io/mambaorg/micromamba:latest

# Set the user to root for file copies and ownership
USER root

# Set the working directory in the container to /home/mambauser/app
WORKDIR /home/mambauser/app

# Copy the interactive-web-app directory contents into the container at /home/mambauser/app
COPY --chown=mambauser interactive-web-app/app.py interactive-web-app/environment.yml .

# Install any needed packages specified in requirements.yml
# Activate the environment by providing ENV_NAME as an environment variable at runtime 
RUN micromamba env create -f environment.yml

# Make port 5006 available for access outside this container
EXPOSE 5006

# Switch to mambauser for the running image
USER mambauser

# Set the command to run when the container is run
CMD ["panel", "serve", "--port", "5006", "app.py", "--allow-websocket-origin=*"]