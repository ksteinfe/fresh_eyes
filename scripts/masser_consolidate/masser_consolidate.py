import os, time, argparse

DELETE_FILES = False
img_ext = "jpg"
mta_ext = "csv"

def main(basepath, do_process_root=False):
    basepath = os.path.abspath(basepath)
    tic = time.clock()

    collected_metadata = []
    for root, dirs, files in walklevel(basepath):
        print("processing {} files".format(len(files)))
        if (not do_process_root) and (root == basepath):
            print("Skipping root directory {}".format(root))
            continue
        label = os.path.split(root)[1]
        for fnm_mta in files:
            bnm_mta, ext_mta = os.path.splitext(fnm_mta)
            if ext_mta != ".{}".format(mta_ext): continue
            fnm_img = "{}.{}".format(bnm_mta,img_ext)
            if fnm_img not in files:
                print("Orphan file found.\t{}\t{}".format(os.path.basename(root),bnm_mta))
                continue

            content = False
            try:
                with open(os.path.join(root,fnm_mta)) as f: content = [x.strip() for x in f.readlines()]
                if len(content) != 1: raise()
                content = content[0] # ONLY READS FIRST LINE OF TEXT FILE
            except:
                print("Trouble reading or parsing: \t{}\t{}".format(label, bnm_mta))
            if not content:
                print("Skipping malformed metadata: \t{}\t{}".format(label,bnm_mta))
                continue

            content = "{},{},{}".format(os.path.join(root, fnm_img), content, label)

            collected_metadata.append(content+"\n")
            if (DELETE_FILES): os.remove(os.path.join(root,fnm_mta))

    if len(collected_metadata)==0:
        print("found no metadata")
        return

    collected_metadata[-1] = collected_metadata[-1].strip()
    f = open(os.path.join(basepath,"_dataset.{}".format(mta_ext)), "w")
    f.writelines(collected_metadata)
    f.close()

    t = round(time.clock()-tic)
    print("time:\t{}s".format(t))



def walklevel(some_dir, level=1):
    some_dir = some_dir.rstrip(os.path.sep)
    assert os.path.isdir(some_dir), "Directory not found:\t{}".format(some_dir)
    num_sep = some_dir.count(os.path.sep)
    for root, dirs, files in os.walk(some_dir):
        yield root, dirs, files
        num_sep_this = root.count(os.path.sep)
        if num_sep + level <= num_sep_this:
            del dirs[:]


if __name__ == '__main__':
    def str2bool(v):
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Boolean value expected.')

    # create main parser
    parser = argparse.ArgumentParser()
    parser.add_argument('root_path', help="path at which to find a collection of subdirectories, each of which should be full of images and metadata.")
    parser.add_argument("--include_root", type=str2bool, nargs='?',
                            const=True, default=False,
                            help="Activate nice mode.")
    args = parser.parse_args()

    main(args.root_path, args.include_root)
