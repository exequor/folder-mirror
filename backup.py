import os
import shutil
import time
import sys
import time
import datetime
import json
import fnmatch
from unittest import skip

#requires pysmb and therefore pyasn1

simulate = False # Do not perform any action
skipDifferentDateTimeCheck = True

if (simulate == True):
    print("SIMULATING")
backup_config = "backupX.json"


the_log = []
the_printed_string = ""

depth = 0
progress_by_depth = []

report_noise = 100
report_iterator = 0

entry_progress = ""

start_timer = time.time()

dot_count = 0

depths = []

def dot():
    global dot_count
    dot_count += 1
    if (dot_count % 1000 == 0):
        print(".", end="")
        if (dot_count % 10000 == 0):
            print(str(time.time()-start_timer))
            #datetime.datetime.now()
            dot_count = 0
            return True
    return False

def reset_depth(depth, total):
    global depths
    depths = depths[0:depth]
    depths.append([0,total])

def update_depth(index, value):
    global depths
    depths[index][0] = value
    
def print_depths():
    global depths
    print("|",end="")
    for depth in depths:
        print("{}/{}|".format(depth[0], depth[1]), end="")
    print("")

def print_report():
    global report_iterator
    global report_noise
    global entry_progress
    global start_timer

    if (report_iterator%report_noise == 0):
        os.system('cls')

        current_timer = time.time() - start_timer
        print( "%02d:%02d|"%(current_timer/60, current_timer%60), end="" )

        outStr = ""
        for i in progress_by_depth:
            if (outStr != ""):
                outStr += "->"
            outStr += i
        print(entry_progress+outStr)
    report_iterator +=1

def backup(filename):
    in_name = "{}/{}".format(source_root, filename)
    out_name = "{}/{}".format(destination_root, filename)
    copy = True;
    dot()
    log = filename+": "
    done = False
    retries = 0
    while(done == False):
        try:
            if (os.path.exists(out_name)):
                time_date_a = time.ctime(os.path.getmtime(out_name))
                time_date_b = time.ctime(os.path.getmtime(in_name))
                
                if (time.ctime(os.path.getmtime(out_name)) != time.ctime(os.path.getmtime(in_name)) and skipDifferentDateTimeCheck == False) :
                    log += "{} has different date.".format(out_name)
                    copy = True
                elif (os.path.getsize(out_name) != os.path.getsize(out_name)):
                    log += "{} has different size.".format(out_name)
                    copy = True
                else:
                    log += "{} is identical".format(out_name)
                    copy = False
            if (copy == True):
                out_dir = os.path.dirname(out_name)
                try:
                    if (simulate == False):
                        os.makedirs(out_dir)
                except:
                    pass
                try:
                    if (simulate == False):
                        shutil.copy(in_name,out_dir)
                        shutil.copystat(in_name,out_name)
                    log += " [copied]\n"
                except:
                    log += " [error]\n"
            else:
                log += " [skipped]\n"
            done = True
        except OSError as e:
            retries += 1
            if (retries > 5):
                done = True
            print("[retrying {}] Os Error {} ({}->{}).  Retrying in 5 seconds".format(retries, e.strerror, in_name, out_name))
            time.sleep(5)
    return log

def scan_dir(root_dir,depth=0, verbose=True, patterns = ["*.*"], exceptions = []):
    global the_log
    rv = []
    nb_files = 0
    #print("Scanning: "+root_dir)
    try:
        entries = os.listdir(root_dir)

        if (depth < 3):
            reset_depth(depth, len(entries))
        i = 0
        for entry in entries:
            if (depth < 3):
                update_depth(depth, i)
                print_depths()
            full_entry = os.path.join(root_dir,entry)
            if (os.path.isfile(full_entry)):
                for p in patterns:
                    dot()
                    if (fnmatch.fnmatch(full_entry, p)):
                        rv += [full_entry]
            else:
                if (not full_entry in exceptions):
                    rv += scan_dir(full_entry, depth = depth+1)
                else:
                    print("SKIPPING {}".format(full_entry))
            i+=1
    except FileNotFoundError as e:
        the_log += ["Folder not found: {}".format(root_dir)]
    # for root,subdirs,files in os.walk(df, ):
    #     for f in files:
    #         for p in patterns:
    #             dot()
    #             if (fnmatch.fnmatch(f, p)):
    #                 #rv+=[root,f]
    #                 #rv += [os.path.normpath("{}/{}".format(root, f))]
    #                 #rv += ["{}/{}".format(root, f)]
    #                 rv += [root+ps+f]
    #                 break
    return rv    

def remove_extra(file_list,prefix):
    global the_log

    files = scan_dir(destination_root, patterns=patterns)

    for f in files:
        dot()
        stripped_file = os.path.relpath(f, destination_root)
        if (stripped_file not in file_list):
            outname = "Trash{}/{}".format(prefix,f)
            try:
                if (simulate == False):
                    os.makedirs(os.path.dirname(outname))
            except:
                pass
            try:
                if (simulate == False):
                    shutil.move(f,outname)
                print ("{} [moved to trash]".format(f))
            except FileNotFoundError:
                the_log += ["File {} could not be removed because of a FileNotFoundError.\n".format(f)]
            except OSError:
                the_log += ["File {} could not be removed because of a OSError.\n".format(f)]
    
            

def remove_empties(base):
    try:
        if not os.listdir(base):
            print ("Removing:"+base)
            if (simulate == False):
                os.rmdir(base)
            return True
        else:
            for f in os.listdir(base):
                dot()
                if (os.path.isdir(base+"/"+f) == True):
                    if (remove_empties(base+"/"+f) == True):
                        return True
    except FileNotFoundError:
        pass
    return False

def time_to_string(t):
    return "%04d/%02d/%02d %02d:%02d"%(t.tm_year,t.tm_mon,t.tm_mday,t.tm_hour,t.tm_min)
    
start_time = time.localtime();
the_log += ["Start Time: "+time_to_string(start_time)]

timestamp = "%04d%02d%02d%02d%02d%02d"%(start_time.tm_year,start_time.tm_mon,start_time.tm_mday,start_time.tm_hour,start_time.tm_min,start_time.tm_sec)
print ("Building File List",)

file_list = []
try:
    f = open("backup.txt", "r")
    lines = f.readlines()
    f.close()

    entry_prog = 0

    for toadd in lines:
        entry_prog += 1
        entry_progress = "%d/%d:"%(entry_prog,len(lines))
        toadd = toadd.strip("\n")
        if (os.path.isdir(toadd)):
            the_log += ["Adding dir:"+toadd]
            file_list += scan_dir(toadd)
        else:
            the_log += ["Adding file:"+toadd]
            file_list += [toadd]

except FileNotFoundError:
    json = json.load(open(backup_config, "r"))
    patterns = json["patterns"]
    source_root = json["source_root"]
    exceptions = []
    for exception in json["exceptions"]:
        exceptions += [os.path.join(source_root, exception)]
    
    #for source in json["sources"]:
    print("Scanning {}".format(source_root))
    file_list += scan_dir("{}".format(source_root), patterns = patterns, exceptions = exceptions)
    destination_root = os.path.normpath(json["destination_root"])
    
    
    #patterns = json["patterns"]
# if (source_root[0:2] == "//"):
#     source_root = "\\{}".format(os.path.normpath(source_root))
# else:
#     source_root = os.path.normpath(source_root)

for k, v in enumerate(file_list):
    file_list[k] = os.path.normpath(file_list[k][len(source_root):].lstrip("\\"))

    #file_list[k] = os.path.relpath(file_list[k], )

print ("done!")
scan_time = time.localtime();
the_log += ["Scanning Complete At: "+time_to_string(scan_time)]

print ("Removing extra files",)
remove_extra(file_list,timestamp)
remove_time = time.localtime();
the_log += ["Scanning Complete At: "+time_to_string(remove_time)]

print ("done!")
print ("Backing up")

i = 0
for f in file_list:
    if (i%100 == 0):
        print ("[{} {}/{}]".format(time.time(),i,len(file_list)))
    i+=1
    the_log += [backup("{}".format(f))]
print ("Cleaning up",)

backup_time = time.localtime();
the_log += ["Backup Complete At: "+time_to_string(backup_time)]

remove_empties(destination_root)
print ("done!")
remove_end_time = time.localtime();
the_log += ["Remove Empties Complete At: "+time_to_string(remove_end_time)]

try:
    os.makedirs("Logs")
except:
    pass

f = open("Logs/Backup"+timestamp+".txt", "w")
for line in the_log:
    try:
        f.write(line)
    except:
        f.write("Line broken")
f.close()

