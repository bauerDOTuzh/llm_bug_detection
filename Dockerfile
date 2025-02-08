# Use Miniconda as base image
FROM continuumio/miniconda3

# Set working directory inside the container
WORKDIR /app

# Copy Conda environment file
COPY environment_docker.yml /app/


# Create Conda environment
RUN conda env create -f /app/environment_docker.yml && conda clean --all -y

# Ensure Conda environment is activated for all subsequent commands
ENV PATH=/opt/conda/envs/infile_vulnerability_localization/bin:$PATH

# copy all files to ensure preservation (-> dockerfile will have also cache, which is too large for github)
COPY 0_dataset_creation /app/0_dataset_creation
COPY 1_all_files_analysis /app/1_all_files_analysis
COPY 2_code_in_the_haystack /app/2_code_in_the_haystack
COPY 3_optimal_position /app/3_optimal_position

# Copy .env.example to .env as a stub
COPY .env.example /app/.env
# rename .env.example to .env
# RUN cp /app/.env.example /app/.env

SHELL ["/bin/bash", "--login", "-c"]
ENV PATH=/opt/conda/envs/infile_vulnerability_localization/bin:$PATH
RUN echo "source activate infile_vulnerability_localization" >> ~/.bashrc

# Expose Jupyter port
EXPOSE 8888

# Start Jupyter (now uses the correct PATH)
CMD ["bash", "-c", "source activate infile_vulnerability_localization && jupyter notebook --ip=0.0.0.0 --port=8888 --allow-root --no-browser"]
