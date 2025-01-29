# TOHMIN

Analyze and visualize the body temperature cycle of hibernating animals.

# Environment Setup Instructions

Steps to build a local execution environment.

Please proceed with the following steps after completing all the preliminary preparations.

- For those using a Docker environment

- For those using a local environment

## Preliminary Preparations

1. Create a GitHub account

    Create a GitHub account with your email address.

2. Install git

    - For those using Homebrew

        ```
        brew install git
        ```

    - For those using an installer

        Download the installer from the [git official website](https://git-scm.com/) and expand it according to the instructions.

    Check if the installation was successful.

    ```
    git --version
    >>> git version X.XX.X
    ```

3. Clone the repository

    When you clone the repository, a folder with the repository name (here, TOHMIN) will be created.

    - Set the location where you want to place it if necessary. You need to change a something.

        ```
        # example
        cd ~ && mkdir something && cd something
        ```
    
    Cloning will create the same folder structure as the repository.

    ```
    git clone https://github.com/HIBlab-ILTS/TOHMIN.git
    ```

## Environment Setup with Docker

1. Install Docker

    - For those using Homebrew
    
        ```
        brew install --cask docker
        ```

    - For those using an installer

        ※ May be charged in some cases, so please consult with your administrator.

        Download the appropriate installer for your chip from [Docker Desktop on Mac](https://docs.docker.com/desktop/install/mac-install/)
        
        Expand the dmg file according to the instructions.


2. Run

    Move to the directory where the Dockerfile is located and execute the following command.

    ```
    # Execute only once
    cd TOHMIN
    docker build -t src .
    docker run -p 8080:8000 src
    ```

    The server will start, so connect to http://localhost:8080/ to use it.

    - How to check analysis results

        Start a new terminal and execute the following.

      - Get Container ID

        ```
        docker ps
        ```
    
      - Enter the server

        ```
        docker exec -it <container_id> /bin/bash
        ```


## Local Environment Setup

1. Install pyenv

    If your shell is `bash`, replace `zsh` with `bash` and execute.

    ```
    brew update
    brew install pyenv

    # For zsh
    echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.zshrc
    echo 'eval "$(pyenv init --path)"' >> ~/.zshrc
    source ~/.zshrc
    ```
        
2. Install python

    ```
    pyenv install 3.12.0
    pyenv global 3.12.0
    ```

    Check if the version is correct.

    ```
    python3 -V
    >>> Python 3.12.0
    ```

3. Install Poetry

    If your shell is `bash`, replace `zsh` with `bash` and execute.

    ```
    curl -sSL https://install.python-poetry.org | python3 -

    # For zsh
    echo 'export PATH="$HOME/.poetry/bin:$PATH"' >> ~/.zshrc
    source ~/.zshrc
    ```

4. Run

    Execute the following command only the first time you clone the repository.

    ```
    # Execute only once
    poetry install
    ```

    Start the application.

    ```
    poetry shell
    cd src
    python app.py
    ```

    Operate from the URL http://localhost:8000 .

    When you are finished working, stop it by executing control+C in the terminal.
