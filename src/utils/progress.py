
def config_parser(config):

    if len(config) != 2 :
        raise ValueError("Config file error")

    train_config = config['train']
    test_config = config['test']

    # input file

    # seperator

    # target line

    return train_config, test_config

def buf_count_newlines_gen(fname):
    def _make_gen(reader):
        b = reader(2 ** 16)
        while b:
            yield b
            b = reader(2 ** 16)
    with open(fname, "rb") as f:
        count = sum(buf.count(b"\n") for buf in _make_gen(f.raw.read))
    return count

def readlines_spinner(file):
    # -*- coding: utf-8 -*-

    import threading
    import sys
    import time
    import os
    import random
    import mmap

    all_spinner =  [
        ["✶","✸","✹","✺","✹","✷"],
        ['⣷','⣷', '⣯', '⣟', '⡿', '⢿', '⣻', '⣽', '⣾']
        #["⣾","⣽","⣻","⢿","⡿","⣟","⣯","⣷"],

    ]
    #spinner = all_spinner[random.randint(0,len(all_spinner))-1]

    spinner = all_spinner[1]
    class spin(threading.Thread):   # not sure what to put in the brackets was (threading.Thread, but now im not sure whether to use processes or not)

        def __init__(self):
            super(spin,self).__init__() # dont understand what this does
            self.flag = False

        def run (self):
            pos=0
            while not self.flag:
                sys.stdout.write("\r Reading files ... "+spinner[pos])
                sys.stdout.flush()
                time.sleep(.15)
                pos+=1
                pos%=len(spinner)

        def cursor_visible(self):
            os.system("tput cvvis")

        def cursor_invisible(self):
            os.system("tput civis")


        def spin_stop(self):
            self.flag = True  #the underscore makes this a private variable ?
            sys.stdout.write('\033[2K\033[1G')
            # sys.stdout.write("\033[2K") # Clear to the end of line
            sys.stdout.flush()

    s = spin()
    s.cursor_invisible()
    s.start()

    tmp = []
    with open(file,'r+b') as f:
        # memory-map the file, size 0 means whole file
        map_file = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        for line in iter(map_file.readline, b""):
            tmp.append(line.decode().rstrip('\n'))
        # close the map
        map_file.close()

        #tmp = f.readlines()

    s.spin_stop()
    s.cursor_visible()

    return tmp


def gen_all_pairs(config, all_encoder):

    from tqdm import tqdm
    import time

    in_file = config['input']
    out_file = config['output']+".all_pair"


    truth =  [t['index'] for t in config['target_columns'] if t['type'] == 'truth'][0]
    target_line = [t['index'] for t in config['target_columns'] if t['type'] != 'truth']
    target_type = { t['index']:t['type'] for t in config['target_columns'] if t['type'] != 'truth'}


    based_encoder = all_encoder[0]

    iterator = iter(based_encoder.inverse_table)

    total_len  = len(based_encoder.inverse_table)*len(all_encoder[1].inverse_table)

    pbar = tqdm(total=total_len)

    start_time = time.time()

    print(f"[Generate all pair of encoder ...]")

    out_lines = []
    while True:
        try:
            uid = next(iterator)
            for iid in all_encoder[1].inverse_table:
                out = f"{uid}:1 {iid}:1\n"
                out_lines.append(out)
                pbar.update(1)

        except StopIteration:
            break
    with open(out_file,'w') as o:
        o.writelines(out_lines)

    elapsed_time  = time.time() - start_time

    print(f"[Generate all pair of encoder done] ... ... cost {elapsed_time:.2f} sec")






def pure_readlines(config):
    import pickle
    import time
    import gc
    import mmap
    import os
    from encoder.encoder import label_encoder, num_encoder

    cache_line = []

    in_file = config['input']
    out_file = config['output']


    truth =  [t['index'] for t in config['target_columns'] if t['type'] == 'truth'][0]
    target_line = [t['index'] for t in config['target_columns'] if t['type'] != 'truth']
    target_type = { t['index']:t['type'] for t in config['target_columns'] if t['type'] != 'truth'}


    try:
        # READ PICKLE
        #if config['cached'] :
        if False:
            all_encoder = {}
            for idx in range(len(target_line)):
                pkl_output_path = "/".join(out_file.split('/')[:-1])+f"/encoder{idx}_dict.pkl"
                with open(pkl_output_path,'rb') as p:
                    all_encoder[idx] = pickle.load(p)

            print("[Get Cache encoder]")

            return all_encoder
    except :
        print("[Get Cache encoder error ...]")
        pass

    start_time = time.time()
    print("[Collecting Feature]")

    labels = [set() for i in range(len(target_line))]



    try:
        from tqdm import tqdm

        print("[Get some reading file info] ...")
        total_len = buf_count_newlines_gen(in_file)
        print("[Get some reading file info] done !!")

        pbar = readlines_spinner(in_file)

        # if has header, just skip the first line(header)
        if config['header']:
            total_len -= 1
            pbar = pbar[1:]

        pbar = tqdm(pbar,total=total_len)
    except ImportError as error:
        with open(in_file,'r') as f:
            pbar = f.readlines()

        # if has header, just skip the first line(header)
        if config['header']:
            pbar = pbar[1:]


    for line in pbar:
        line = line.rstrip('\n').split(config['seperator'])
        #t_line = []
        for i, t in enumerate(target_line):
            feat = line[t]
            if len(feat.split()) > 1:
                # list of tuple case
                if target_type[t] == 'list_category':
                    for l in feat.split():
                        for ll in l.split(','):
                            labels[i].add(ll)
                    #t_line.append(feat.split())
                # list case
                else:
                    for l in feat.split():
                        labels[i].add(l)
                    #t_line.append(feat.split())

            # general case
            else:
                labels[i].add(feat)
                #t_line.append(feat)

        #t_line.append(line[truth])


    del pbar

    elapsed_time = time.time()-start_time

    print(f"[Collecting Feature done] ... ...  cost {elapsed_time:.2f} sec\n")


    start_time = time.time()
    print("[Encoding start]")
    last_feat_len = 0
    all_encoder = {}
    # iterate all set of feat (column)
    for idx, feat in enumerate(labels):
        # first column no last_feat_len
        if idx == 0:
            if target_type[idx]=='num':
                all_encoder[idx] = num_encoder()

            elif target_type[idx] == 'cat':
                all_encoder[idx] = label_encoder(offset=1,shared=True)
            last_feat_len = len(feat)

        else:
            if target_type[idx]=='num':
                # +1 for the shared_idx
                all_encoder[idx] = num_encoder(last_feat_len+1)

            elif target_type[idx] == 'cat':
                 # +1 for the shared_idx
                all_encoder[idx] = label_encoder(last_feat_len+1,shared=True)

            last_feat_len = len(feat)

        all_encoder[idx].fit(feat)

    elapsed_time = time.time()-start_time

    # Write pickle
    if config['cached'] and False:
        for idx, _encoder in all_encoder.items():
            pkl_output_path = "/".join(out_file.split('/')[:-1])+f"/encoder{idx}_dict.pkl"
            with open(pkl_output_path,'wb') as p:
                pickle.dump(_encoder.inverse_table,p)

    print(f"[Encoding done] ... ... cost {elapsed_time:.2f} sec\n")

    # free memory
    del labels
    gc.collect()


    gen_output_file(config, all_encoder)

    return all_encoder

def print_lines(outputs):
    print("-"*15)
    for line in outputs:
        print(line)


def gen_output_file(config, all_encoder,truth_line=True):
    import pickle
    import time
    import gc
    import mmap
    import os
    from tqdm import tqdm
    from scipy.sparse import coo_matrix
    import numpy as np

    in_file = config['input']
    out_file = config['output']

    truth =  [t['index'] for t in config['target_columns'] if t['type'] == 'truth']

    if truth_line:
        truth = truth[0]

    target_line = [t['index'] for t in config['target_columns'] if t['type'] != 'truth']

    target_type = { t['index']:t['type'] for t in config['target_columns'] if t['type'] != 'truth'}

    start_time = time.time()
    print(f"[Generate output]")



    '''
    for sparse format
    '''
    row = []
    col = []
    data = []


    total_len = buf_count_newlines_gen(in_file)
    out_lines = []
    with open(out_file,"w") as o:
        with open(in_file, "r+b") as f:
            map_file = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
            iter_mfile = iter(map_file.readline, b"")
            if config['header']:
                next(iter_mfile)
            pbar = tqdm(iter_mfile, total=total_len)
            ## iterate all instance
            for r_idx, line in enumerate(pbar):
                line = line.decode()
                line = line.rstrip().split(config['seperator'])
                out = []


                ## iterate all feature
                for i, t in enumerate(target_line):
                    enc = all_encoder[i]
                    feat = line[t]
                    feat_len = len(feat.split())
                    # list case
                    if feat_len > 1:
                        # list of tuple case
                        if target_type[t] == 'list_category':
                            feat_len = len(feat.split(','))
                            for l in feat.split(','):
                                for ll in l.split():
                                    one_hot = enc.transform(ll)
                                    out.append("{}:{:.4f} ".format(one_hot,1/feat_len))
                        # list case
                        else:
                            for l in line[t].split():
                                one_hot = enc.transform(l)
                                out.append("{}:{:.4f} ".format(one_hot,1/feat_len))
                    # general case
                    else:
                        one_hot = enc.transform(line[t])
                        out.append("{}:1 ".format(one_hot))
                        if config['sparse']:
                            row.append(r_idx)
                            col.append(one_hot)
                            data.append(1)

                if truth_line:
                    output = line[truth] + " " +" ".join(out)
                    if config['sparse']:
                        row.append(r_idx)
                        col.append(0)
                        data.append(float(line[truth]))

                else:
                    output = " ".join(out)


                output += '\n'
                if config['cached']:
                    out_lines.append(output)
                else:
                    o.write(output)

        if config['cached']:
            o.writelines(out_lines)







        #print(sparse_output.toarray())
    elapsed_time = time.time()-start_time

    print(f"[cached done] ... ... cost {elapsed_time:.2f} sec\n")

    #print_lines(out_lines)
    if config['sparse']:
        np_row = np.array(row)
        np_col = np.array(col)
        np_data = np.array(data)

        n = len(all_encoder[len(all_encoder)-1].table)

        #print(r_idx, n)

        # shape +=1 , becausing the zero indexing
        sparse_output = coo_matrix((np_data, (np_row, np_col)), shape=(r_idx+1,n+1))

        gen_sparse_np(sparse_output,config)

        #gen_sparse_h5(sparse_output,config)

    # free memory
    del out_lines
    gc.collect()

def gen_sparse_np(matrix,config):
    from scipy import sparse
    out_file = config['output']+".npz"
    sparse.save_npz(out_file, matrix)

def gen_sparse_h5(matrix, config):
    import h5py

    out_file = config['output']+".h5"
    f = h5py.File(out_file,'w')
    g = f.create_group('Mcoo')
    g.create_dataset('data', data=matrix.data)
    g.create_dataset('row', data=matrix.row)
    g.create_dataset('col', data=matrix.col)
    g.attrs['shape'] = matrix.shape
    f.close()
