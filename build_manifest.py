'''
    Intended to be run on non-microcontroller device.
    Tested only on Windows

    Builds a pretty formatted manifest.json file which can be used to
    update remote microcontrollers using their svc_git.py service.

    This program is run after updates are made to the github repo. The
    generated manifest.json is then checked into the repo. Remote devices
    can then run their update process.

    Remote devices read the generated manifest.json file. The local copy 
    of manifest.json is compared to the repo version of manifest.json 
    by svc_git.py:
      - Update files where the sha value has changed
      - Delete files which are not in the repo manifest.json file
      - Add files which are in the repo manifest but not in the local copy

    Once that is completed, the remote device replaces the local copy
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
        json.dump(o, f, sort_keys=True)
        
# convert a list to a dictionary
def cnv_list_to_dict(lst,key):
    r = {}
    for ent in lst:
        r[ent[key]] = ent
        
    return r        

# synch local directory with git
def sync_dir(local,git):

    if local["sha"] == git["sha"]:
        print("no changes in directory",local["name"])
        return 
    
    # update local sha
    local["sha"] = git["sha"]
    directory = local["name"]
    
    print("update directory",directory)
    
    git_mani = get_github_manifest(directory)
    git_mani = cnv_list_to_dict(git_mani,"name")
    
    for local_file in local["files"].copy():
        fn = local_file["name"]
        if not fn in git_mani:
            local["files"].remove(local_file)
            print("...removed",fn)
        else:
            git = git_mani[fn]
            if local_file["sha"] != git["sha"]:
                print("...update","/"+directory+"/"+fn)
                local_file["sha"] = git["sha"]
                
            # remove from the git manifest to detect new files
            del git_mani[fn]
            
    # At this point, all git manifest items that are in
    # the local file have been deleted from the
    # git manifest dictionary. Therefore all remaining
    # git manifest items are new to local file system
        
    for git_obj in git_mani.values():
        # ignore any non-file entries
        if git_obj["type"] != "file":
            continue
        
        name = git_obj["name"]
        sha  = git_obj["sha"]
        new_entry = {"name":name,"sha":sha}
        
        local["files"].append(new_entry)
        print("...add "+"/"+directory+"/"+name)
        # save_git_file("/"+directory+"/"+name)
            


def update(fn):
    print("checking repo changes")
    local = load_json(fn)
    
    # get github manifest for root directory
    # and convert to a dictionary
    git = get_github_manifest("")
    git = cnv_list_to_dict(git,"name")

    for local_obj in local["obj"]:
        
        # error if local object no longer in git
        git_obj = git[local_obj["name"]]
        if "files" in local_obj:
            sync_dir(local_obj,git_obj)
        else:
            sha = git_obj["sha"]
            fn  = git_obj["name"]

            if local_obj["sha"] != sha:
                print("update",fn)
                local_obj["sha"] = sha
            
    # save_json(fn,local)
    return local

fn = "manifest.json"
new_manifest = update(fn)

if new_manifest != None :
    save_json(fn,new_manifest)
    