"""
    Update from Git Service Class - Part 2
    
    Runs in report mode or update mode.
    
    Add, change and delete files by comparing the local
    manifest.json file with the current github manifest.json file.
    
"""

from psos_svc import PsosService
import uasyncio
import queue
import urequests
import gc
import os

import psos_util
from svc_msg import SvcMsg

import secrets
import ujson

class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        self.sha     = None
        self.manifest= None
        self.test_mode = self.get_parm("test",True)
    
    async def run(self):
        
        mqtt = self.get_mqtt()

        # wait until mqtt is ready
        while mqtt._client == None:
            await uasyncio.sleep_ms(1000)
        
        self.restore_config() # in case we crash
        
        if self.test_mode:
            self.log("test mode only")
        else:
            self.log("git update mode")
        
        # load current local version of manifest
        self.manifest= psos_util.load_json("manifest.json")
        
        await self.update()
        
        await self.log("git pull complete")
        self.reset(rsn="git pull complete")

    # Restore config so it will run the original device
    # parms instead of the git update parms
    def restore_config(self):
        config = self.get_parm("config")
        # config["device"] = config["o_device"]
        # del config["o_device"]
        config["fn_parms"]   = config["o_fn_parms"]
        del config["o_fn_parms"]
        self.save_json("config.json",config)
        
    # update sourc from github.
    # update manifest with new sha
    async def update(self):
        # read github manifest file as generated 
        # by buid_manifest.py run on local PC
        self.display_lcd_msg("read github\nmanifest.json")
        await self.log("read github manifest.json")
        git = await self.get_github_file("manifest.json")
        git = ujson.loads(git)
        git = self.cnv_list_to_dict(git["obj"],"name")

        for local_obj in self.manifest["obj"]:
            
            # ignore if local object no longer in git
            name = local_obj["name"]
            if name in git:
                git_obj = git[name]
                if "files" in local_obj:
                    await self.sync_dir(local_obj,git_obj)
                else:
                    await self.sync_file(local_obj,git_obj,dir="")

    async def sync_dir(self,local,git):
        if local["sha"] == git["sha"]:
            self.display_lcd_msg("no update to dir\n"+local["name"])
            await self.log("no update to dir "+local["name"])
            return
            
        directory = local["name"]
        
        self.display_lcd_msg("updating\n"+directory)
        await self.log("updating "+directory)
        
        git_mani = git["files"] # list of files
        git_mani = self.cnv_list_to_dict(git_mani,"name")

        await self.chg_del_files(local,git_mani,directory)      
        await self.add_new_files(local,git_mani,directory)

    # Delete and change files on local file system.
    # Delete processed file names from the git manifest.
    # Remaining git manifest files names are then all new files.
    async def chg_del_files(self,local,git_mani,directory):
        self.display_lcd_msg("chg & del\nfiles")
        await self.log("change and delete files")
        for local_file in local["files"].copy():
            fn = local_file["name"]
            if not fn in git_mani:
                self.display_lcd_msg("delete file\n"+directory+"/"+fn)
                self.log("delete file "+directory+"/"+fn)
                self.delete_file(directory+"/"+fn)
            else:
                git = git_mani[fn]
                await self.sync_file(local_file,git,directory)
                del git_mani[fn]

    # files remaining in git manifest were not found in
    # the local manifest. Add them to the local file system
    async def add_new_files(self,local,git_mani,directory):
        for git_obj in git_mani.values():
            await self.save_git_file(directory+"/"+name)
            
    async def sync_file(self,local,git,dir=""):
        if local["sha"] == git["sha"]:
            return False
        
        fn = local["name"]
        if dir != "":
            fn = dir+"/"+fn
            
        await self.save_git_file(fn)

    async def save_git_file(self,fn):
        f = await self.get_github_file(fn)
        self.display_lcd_msg("save file\n"+fn)
        await self.log("save file "+fn)
        
        # comment out below for testing
        if not self.test_mode:
            self.write_file(fn,f) 
          
    # this is the only read of github files
    async def get_github_file(self,fn,windows=True):
        await uasyncio.sleep_ms(0)
        self.display_lcd_msg("read git file\n{}".format(fn))
        await self.log("read git file {}".format(fn))
        gc.collect()

        uri = "https://raw.githubusercontent.com/ddgarrett/psos/main/{}".format(fn)
        r = urequests.get(uri)
        c = psos_util.to_str(r.content)
        r.close()
        
        # if windows, replace \n with \r\n
        if windows: 
            c = c.replace("\n","\r\n")
            
        gc.collect()
        await uasyncio.sleep_ms(0)
        return c
    
    # save object o to file named "fn"
    def save_json(self,fn,o):
        with open(fn, "w") as f:
            ujson.dump(o, f)

    # convert a list to a dictionary
    def cnv_list_to_dict(self,lst,key):
        r = {}
        for ent in lst:
            r[ent[key]] = ent
            
        return r
    
    def write_file(self,fn,o):
        with open(fn, "w") as f:
            f.write(o)
            
    def delete_file(self,fn):
        if not self.test:
            try:
                os.remove(fn)
            except:
                print("...remove file not found:",fn)
