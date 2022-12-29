
import wifi
import urequests
import psos_util
import ujson

def get_github_file(fn,windows):
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

def get_repo_sha(headers={"User-Agent":"ddgarrett"}):
    uri = "https://api.github.com/repos/ddgarrett/psos/git/refs"
    r = urequests.get(uri,headers=headers)
    c = r.json()
    r.close()
    return c[0]["object"]["sha"]

def save_file_local(fn,c):
    f = open(fn, "w")
    f.write(c)
    f.close()
    
# save object o to file named "fn"
def save_json(fn,o):
    with open(fn, "w") as f:
        ujson.dump(o, f)

'''
fn = "base/cmd_blink.py"
c = get_github_file(fn,windows=True)
write_file(fn,c)


files = ["main.py",]
parms = "r02.psos_parms.json"
m = get_github_manifest("")
'''

def update():
    print("checking repo changes")
    cm = psos_util.load_json("manifest.json")
    sha = get_repo_sha()

    if cm["sha"] == sha:
        return "no changes to repo"

    for s in cm:
        m = gt_github_manifest(s["dir"])
        
        # if s["sha"] != m
        
        if not s["sync"]:
            update_files(s["files"],m)
        else:
            sync_dir()
        

r = update()
print(r)



