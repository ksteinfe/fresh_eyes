from PIL import Image
import os, argparse, csv

whitelist_ext = ['jpg','png']

def main(pth_src, dst_name):
    rows = [["image", "label"]]
    labels = [f for f in os.listdir(pth_src) if os.path.isdir(os.path.join(pth_src, f))]
    print("found {} directories that may contain images:\n{}".format(len(labels), labels))

    for label in labels:
        pth_lbl = os.path.join(pth_src,label)
        fnames = [f for f in os.listdir(pth_lbl) if os.path.isfile(os.path.join(pth_lbl, f))]
        fnames = [f for f in fnames if any([f.endswith(ext) for ext in whitelist_ext])]
        print("found {} image files in directory {}.".format(len(fnames),label))
        for fname in fnames:
            row = os.path.join(label,fname),label
            rows.append(row)

    dst_name = dst_name.lower()
    if not dst_name.endswith('.csv'): dst_name = dst_name + '.csv'
    with open(os.path.join(pth_src,dst_name), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    f.close()

if __name__ == '__main__':
    # create main parser
    parser = argparse.ArgumentParser()
    parser.add_argument('src_path', help="path at which to find directories of source images. all JPG and PNG files will be processed.")
    parser.add_argument('dst_name', help="filename for the resulting CSV file. will be saved at the directory defined by src_path")
    args = parser.parse_args()

    main(args.src_path, args.dst_name)
