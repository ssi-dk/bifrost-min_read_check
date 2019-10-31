#!/usr/bin/env python3
"""
Launcher file for accessing dockerfile commands
"""
import argparse
import json
import subprocess
import os
from bifrostlib import datahandling

COMPONENT = datahandling.load_yaml(os.path.join(os.path.dirname(__file__), 'config.yaml'))

def parse_args():
    """
    Arg parsing via argparse
    """
    description = (
        f"-Description------------------------------------\n"
        f"{COMPONENT['details']['description']}"
        f"------------------------------------------------\n\n"
        f"*Run command************************************\n"
        f"docker run \ \n"
        f" -e BIFROST_DB_KEY=mongodb://<user>:<password>@<server>:<port>/<db_name> \ \n"
        f" -v <input_path>:/input \ \n"
        f" -v <output_path>:/output \ \n"
        f" {COMPONENT['dockerfile']} \ \n"
        f"    -id <sample_id>\n"
        f"************************************************\n"
    )
    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-id', '--sample_id',
                        action='store',
                        type=str,
                        help='Sample ID of sample in bifrost, sample has already been added to the bifrost DB')
    parser.add_argument('--install',
                        action='store_true',
                        help='Install component')
    parser.add_argument('-info', '--info',
                        action='store_true',
                        help='Provides basic information on component')
    args = parser.parse_args()

    if not datahandling.check_db_connection_exists():
        message = (
            f"ERROR: Connection to DB not establised.\n"
            f"please ensure env variable BIFROST_DB_KEY is set and set properly\n"
        )
        print(message)
    else:
        print(datahandling.get_connection_info())


    if args.info:
        show_info()
    elif args.install:
        install_component()
    elif args.sample_id is not None:
        run_sample(args)


def show_info():
    """
    Shows information about the component
    """
    message = (
        f"Component: {COMPONENT['name']}\n"
        f"Version: {COMPONENT['version']}\n"
        f"Details: {json.dumps(COMPONENT['details'], indent=4)}\n"
    )
    print(message)


def install_component():
    component = datahandling.get_components(component_names=[COMPONENT['name']], component_versions=[COMPONENT['version']])
    if len(component) == 1:
        print(f"Component has already been installed")
    elif len(component) > 1:
        print(f"Component exists multiple times in DB, please contact an admin to fix this in order to proceed")
    else:
        datahandling.post_component(COMPONENT)
        component = datahandling.get_components(component_names=[COMPONENT['name']], component_versions=[COMPONENT['version']])
        if len(component) != 1:
            print(f"Error with installation of {COMPONENT['name']} v:{COMPONENT['version']} \n")
            exit()


def run_sample(args: object):
    """
    Runs sample ID through snakemake pipeline
    """
    sample = datahandling.get_samples(sample_ids=[args.sample_id])
    component = datahandling.get_components(component_names=[COMPONENT['name']], component_versions=[COMPONENT['version']])
    if len(component) == 0:
        print(f"component not found in DB, would you like to install it (Y/N)?:")
        install = input()
        if str(install).upper() == "Y":
            datahandling.post_component(COMPONENT)
            component = datahandling.get_components(component_names=[COMPONENT['name']], component_versions=[COMPONENT['version']])
            if len(component) != 1:
                print(f"Error with installation of {COMPONENT['name']} v:{COMPONENT['version']} \n")
                exit()
        else:
            print(f"To continue please install the component")
            exit()

    if len(sample) == 0:
        # Invalid sample id
        print(f"sample_id not found in DB")
        pass
    elif len(sample) != 1 or len(component) != 1:
        print(f"Error with sample_id or component_id")
    else:
        print(f"snakemake -s /bifrost/{COMPONENT['name']}/pipeline.smk --config sample_id={str(sample[0]['_id'])} component_id={str(component[0]['_id'])}")
        process = subprocess.Popen(f"snakemake -s /bifrost/{COMPONENT['name']}/pipeline.smk --config sample_id={str(sample[0]['_id'])} component_id={str(component[0]['_id'])}",
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   shell=True)
        process_out, process_err = process.communicate()
        print(process_out, process_err)


if __name__ == '__main__':
    parse_args()
