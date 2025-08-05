from importlib.metadata import version


def get_version():
    try:
        return version("cemento")
    except Exception:
        return None


DEFAULT_DOWNLOADS = {
    # cco as the default download
    "cco": "https://raw.githubusercontent.com/CommonCoreOntology/CommonCoreOntologies/refs/heads/develop/src/cco-merged/CommonCoreOntologiesMerged.ttl"
}


header = rf"""
  ____ _____ __  __ _____ _   _ _____ ___  
 / ___| ____|  \/  | ____| \ | |_   _/ _ \ 
| |   |  _| | |\/| |  _| |  \| | | || | | |
| |___| |___| |  | | |___| |\  | | || |_| |
 \____|_____|_|  |_|_____|_| \_| |_| \___/ 

{get_version()}. Building the road to ontologies for materials data.
Copyright 2025 CWRU SDLE-MDS3
"""
