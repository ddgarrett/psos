'''
    Intended to be run on non-microcontroller device.
    Tested only on Windows

    Builds a pretty formatted manifest.json file which can be used to
    update remote microcontrollers using their svc_git.py service.

    This program is run after updates are made to the github repo. The
    generated manifest.json is then checked into the repo. Remote devices
    can then run their update process using the sha of that manifest.json file.

    Remote devices read the generated manifest.json file. The local copy 
    of manifest.json is compared to the repo version of manifest.json 
    by svc_git_upd.py:
      - Update files where the sha value has changed
      - Delete files which are not in the repo manifest.json file
      - Add files which are in the repo manifest but not in the local copy

    During that process the remote device replaces the local copy
    of the manifest.json file with the repo version.
'''

import requests
import json
import sys

sys.path.extend([".\lib",".\\base"])

import secrets

headers = {
    "User-Agent"    : "ddgarrett",
    "Authorization" : "Bearer " + (secrets.git_token),
    "Accept"        : "application/vnd.github+json"
}

parms = {
    "uri"  : "https://api.github.com/repos",
    "user" : "ddgarrett",
    "repo" : "psos"
}
    
# read a github manifest file for a directory
def get_github_manifest(dir):
    parms["dir"] = dir
    uri = "{uri}/{user}/{repo}/contents/{dir}".format(**parms)
    print("... reading git dir:",uri)
    r = requests.get(uri,headers=headers)
    c = r.json()
    r.close()
    return c

# load a json file
def load_json(fn):
    # read the paramter file
    with open(fn) as f:
        parms = json.load(f)
        return parms

    return None
    
# save object o to file named "fn"
def save_json(fn,o):
    with open(fn, "w") as f:
        # json.dump(o, f, sort_keys=True, indent=4)
        json.dump(o, f, indent=1)
        
# convert a list to a dictionary
def cnv_list_to_dict(lst,key):
    r = {}
    for ent in lst:
        r[ent[key]] = ent
        
    return r        

# return the list of files and file sha for a given directory
# returns the list of files 
def rebuild_dir(name):
    print("rebuild directory",name)
    files = []

    # get github manifest for directory
    git = get_github_manifest(name)
    
    for obj in git:
        if obj["type"] == "file":
            e = {"name": obj["name"],
                 "sha" : obj["sha"] }
            files.append(e)

    print("... {} files in dir {}".format(len(files),name))
    return files


# rebuild the manifest using the initial manifest
# defined in filename (fn)
def rebuild_manifest(fn):
    print("rebuilding manifest")
    manifest = load_json(fn)

    # get github manifest for root directory
    # and convert to a dictionary
    git = get_github_manifest("")
    git = cnv_list_to_dict(git,"name")

    for obj in manifest["obj"]:
        obj["sha"] = git[obj["name"]]["sha"]
        if "files" in obj:
            obj["files"] = rebuild_dir(obj["name"])
            
    return manifest


# new_manifest = update(fn)
manifest = rebuild_manifest("manifest_initial.json")
save_json("manifest.json",manifest)
    