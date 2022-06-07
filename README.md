# Master Thesis

The following data extraction and data analyses was conducted in scope of my masters thesis and aimed at
research on effects of the Collective Code Ownership principle. It is based on real project data, but all
personal data was pseudonymised and confident information has been removed.

Developed with ♡ by Joscha Nassenstein


## Prerequisites

It is required to have Python >=3.10 installed in order to run the application.

### Creating and activating the virtual environment

The application makes use of some external dependencies. They need to be installed
before the main script can be executed. The following instructions assume that you are working on
the command line and are currently located at the root folder of this project.

I recommend to create a virtual environment first. When Python was successfully installed
and is available on the command line, this can be archieved via:

`python -m venv .venv`

This will create a new virtual environment in the folder `.venv` at the root of the project.
After creation, it has to be activated in order to install the dependencies:

`.venv/bin/activate` (Linux/Mac) or `.venv\Scripts\activate` (Windows)

### Installing the dependencies

Now the dependencies can be installed. They are listed in the `requirements.txt` file and
pinned to specific versions. This can be done via:

`python -m pip install -r requirements.txt`

Now everything is prepared to run the actual application

### Configure credentials for AWS and GitLab

The application leverages interfaces to GitLab and AWS to extract data from there:

- GitLab uses a token which can be created on the web interface. The token is stored in the `secrets.yaml` file.
- AWS uses access keys yielded by the AWS CLI. Those have to be stored in a profile which has the same name as the AWS account which should be accessed.

Without specifying the credentials, it is still possible to view the data and analyses (see below).


## Running the application / extraction processes

What I reference to as application is the data extraction part of the research. Those steps are wrapped in a console application which will run the extraction tasks in parallel in the background.

The application can be started by executing the main script: `python main.py`.
It support multiple arguments to fetch data a specific set of sources. All options can be listed via `python main.py -h`.

In order to only view data, you do not need to have any credentials at hand. Therefore only execute the command from above without any further arguments.


## View the analyses

The analyses are located in the `analyze` folder and make use of the data which was previously extracted by the console application.
The are contained in Jupyter Notebooks, which features a webinterface.
It can be started by running `jupyter notebook` from the command line.

Feel free to browse through the files in the `analyze` folder and view the results of the research done in scope of the masters thesis.
You can also take a look at the `master-thesis.pdf`.

Be warned: The analyses and the thesis itself are written in German.
