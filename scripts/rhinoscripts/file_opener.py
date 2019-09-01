import rhinoscriptsyntax as rs
import os, time

def main():
    basepath = r"C:\Users\kstei\Box\SG 2018 Sample Files for Participants\Datasets\House Types\3dm"
    
    max_flrs = 99 # maximum number of folders to open
    max_fils = 99 # max number of files to open per folder
    
    folder_tic = time.clock()
    fdr_cnt = 0
    for root, dirs, files in walklevel(basepath):
        
        print ("{}\t {}".format(fdr_cnt,root))
        #if (root == basepath): continue
        
        fil_cnt = 0
        for full_filename in files:
            filename, file_extension = os.path.splitext(full_filename)
            if file_extension != ".3dm": continue
            
            file_tic = time.clock()
            filepath = os.path.join(root, full_filename)
            rs.DocumentModified(False)
            rs.Command('_-Open {} _Enter'.format('"'+filepath+'"'))
            t = round(time.clock()-file_tic)
            print(filename+"\ttime:\t"+str(t))
            
            fil_cnt+=1
            if fil_cnt > max_fils: break
        
        fdr_cnt+=1
        if fdr_cnt > max_flrs: break
    
    t = round(time.clock()-folder_tic)
    print("TOTAL\ttime:\t"+str(t))


def walklevel(some_dir, level=1):
    some_dir = some_dir.rstrip(os.path.sep)
    assert os.path.isdir(some_dir), "Directory not found:\t{}".format(some_dir)
    num_sep = some_dir.count(os.path.sep)
    for root, dirs, files in os.walk(some_dir):
        yield root, dirs, files
        num_sep_this = root.count(os.path.sep)
        if num_sep + level <= num_sep_this:
            del dirs[:]
            

if __name__ == "__main__":
    # execute only if run as a script
    main()