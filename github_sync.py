
import wifi
import urequests
import psos_util
import ujson
import os

def get_github_file(fn,windows=True):
    uri = "https://raw.githubusercontent.com/ddgarrett/psos/main/{}".format(fn)
    r = urequests.get(uri)
    c = psos_util.to_str(r.content)
    r.close()
    
    # if windows, replace \n with \r\n
    if windows: 
        c = c.replace("\n","\r\n")
        
    return c
    
def get_github_manifest(dir,headers={"User-Agent":"ddgarrett"}):
    uri = "https://api.github.com/repos/ddgarrett/psos/contents/{}".format(dir)
    r = urequests.get(uri,headers=headers)
    c = r.json()
    r.close()
    return c

# returns sha of refs/heads/main
# future: specify which "ref" to sync with?
def get_repo_sha(headers={"User-Agent":"ddgarrett"}):
    uri = "https://api.github.com/repos/ddgarrett/psos/git/refs/heads/main"
    r = urequests.get(uri,headers=headers)
    c = r.json()
    r.close()
    return c["object"]["sha"]

def save_file_local(fn,c):
    f = open(fn, "w")
    f.write(c)
    f.close()
    
def delete_file(fn):
    print("...remove file",fn)
    try:
        os.remove(fn)
    except:
        print("...remove file not found:",fn)
    
# save object o to file named "fn"
def save_json(fn,o):
    with open(fn, "w") as f:
        ujson.dump(o, f)
        
# convert a list to a dictionary
def cnv_list_to_dict(lst,key):
    r = {}
    for ent in lst:
        r[ent[key]] = ent
        
    return r        
    
def sync_file(local,git,dir=""):
    sha = git["sha"]
    if local["sha"] == sha:
        print("no change in file",local["name"])
        return False
    
    local["sha"] = sha
    fn = local["name"]
    if dir != "":
        fn = "/"+dir+"/"+fn
        
    print("-- update file ",fn)

# synch local directory with git
def sync_dir(local,git):

    if local["sha"] == git["sha"]:
        print("no changes in directory",local["name"])
        return (0,0,0) 
    
    add = chg = delete = 0
    
    # update local sha
    local["sha"] = git["sha"]
    directory = local["name"]
    
    print("update directory",directory)
    
    git_mani = get_github_manifest(directory)
    git_mani = cnv_list_to_dict(git_mani,"name")
    
    for local_file in local["files"].copy():
        fn = local_file["name"]
        if not fn in git_mani:
            delete_file("/"+directory+"/"+fn)
            local["files"].remove(local_file)
        else:
            git = git_mani[fn]
            if local_file["sha"] != git["sha"]:
                print("...update","/"+directory+"/"+fn)
                local_file["sha"] = git["sha"]
                
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
            
                

'''
fn = "base/cmd_blink.py"
c = get_github_file(fn,windows=True)
write_file(fn,c)


files = ["main.py",]
parms = "r02.psos_parms.json"
m = get_github_manifest("")
'''


def update(fn):
    print("checking repo changes")
    local = psos_util.load_json(fn)
    sha = get_repo_sha()

    if local["sha"] == sha:
        return "no changes to repo"
    
    # update local sha
    local["sha"] = sha
    print("repo changed - checking files & directories")
    
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
            sync_file(local_obj,git_obj,dir="")
            
    save_json(fn,local)
    return "ok"

r = update("manifest.json")
print(r)



