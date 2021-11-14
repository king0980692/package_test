from .utils import progress
from .encoder.encoder import label_encoder, num_encoder

import os
import json
import argparse
import readline

def conf_wiz():
    readline.parse_and_bind("tab: complete")
    #readline.set_completer(completer)


    train_inFile = input("Enter the train input file     : ")
    #train_inFile = "./data/ml-100k/ua.base"


    train_sep = input("Enter the train input file sep    : ")

    if train_sep == '\\t':
        train_sep = '\t'


    train_cached = input("Using cached  ?  : [y/n] ")
    train_cached = True if train_cached == 'y' else False

    train_header = input("Is dataset contains header  ?  : [y/n] ")
    train_header = True if train_header == 'y' else False

    train_sparse = input("Using coo format as output  ?  : [y/n] ")
    train_sparse = True if train_sparse == 'y' else False


    with open(train_inFile, 'r') as f:
        line = f.readline().rstrip()
        target_line = []
        print(f"\n\nThis is the first row of input file \n{line}")
        for idx, l in enumerate(line.split(train_sep)):
            keep = input(f"keep col-{idx}: \n\n\t{l} ? : [y/n] ")
            keep = False if keep == "n" else True
            if keep:
                col_type = input(f"\n\tcol type ? : [cat, num,truth] ")
                target_line.append({"index": idx, "type": col_type})

    print("\n")
    train_outFile = input("Enter the output file     : ")

    train_config = {
        "input": train_inFile,
        "output": train_outFile,
        "cached": train_cached,
        "seperator": train_sep,
        "header": train_header,
        "sparse": train_sparse,
        "target_columns": target_line
    }

    #train_config = json.dumps(train_config, indent=4)

    print("=" * 30, end="\n\n")

    test_inFile = input("Enter the test input file     : ")
    test_sep = input("Enter the test input file sep    : ")

    if test_sep == '\\t':
        test_sep == '\t'

    test_cached = input("Using cached  ?  : [y/n]")
    test_cached = True if test_cached == 'y' else False

    test_header = input("Is dataset contains header  ?  : [y/n]")
    test_header = True if test_header == 'y' else False

    with open(test_inFile, 'r') as f:
        line = f.readline()
        target_line = []
        print(f"This is the first row of input file \n{line}")
        for idx, l in enumerate(line.split(train_sep)):
            keep = input(f"keep col-{idx}: \n\n\t{l} ? : [y/n] ")
            keep = False if keep == "n" else True
            if keep:
                col_type = input(f"\n\tcol type ? : [category,numeric,truth] ")
                target_line.append({"index": idx, "type": col_type})

    test_outFile = input("Enter the output file     : ")

    test_config = {
        "input": test_inFile,
        "output": test_outFile,
        "cached": test_cached,
        "seperator": test_sep,
        "header": test_header,
        "target_columns": target_line
    }
    #test_config = json.dumps(test_config, indent=4)

    config = {"train": train_config, "test": test_config}

    config_json = json.dumps(config, indent=4)

    print(config_json)

    config_path = input("Enter the config store path   : ")

    with open(config_path, "w") as f:
        f.write(config_json)

    return config

def get_config():

    # Arguments
    parser = argparse.ArgumentParser(description="encoder for csv-like file")

    # load params from config file
    parser.add_argument('-c', '--config', help='Path to configuration file')

    parser.add_argument('-i', '--input', help='Path to input file')
    parser.add_argument('-o', '--output', help='Path to output file')
    parser.add_argument('-s',
                        '--seperator',
                        help='Specifiy the seperator to split column')
    parser.add_argument('-b',
                        '--sparse',
                        help='Using coo matrix as output format')
    parser.add_argument('-hh',
                        '--header',
                        default=True,
                        type=bool,
                        help='Specifiy the seperator to split column')
    parser.add_argument('-cc',
                        '--cached',
                        default=True,
                        type=bool,
                        help='Specifiy using cache or not')
    parser.add_argument('-t',
                        '--target_columns',
                        help='Specify the target columns to encode')


    args = parser.parse_args()

    config = args.config

    # if no argument pass in
    if args.input == None and args.config == None:
        config = conf_wiz()

        train_config, test_config = progress.config_parser(config)
        return train_config, test_config




    if config:
        with open(args.config, 'r') as f:
            config = json.load(f)
            train_config, test_config = progress.config_parser(config)
            return train_config, test_config
    else:
        config = vars(args)
        target_idx = {}
        target_col = {}
        target_idx, target_col = config['target_columns'].split(':')

        config['target_columns'] = []

        for idx, _type in zip(target_idx.split(','), target_col.split(',')):
            config['target_columns'].append({"index": int(idx), "type": _type})
        return config, {}

    raise ValueError("Only support json.config file now")


def check_config(config):

    if not os.path.isfile(config["input"]):
        raise ValueError("Input file is not exist")

    if config["seperator"] == '\\t':
        config["seperator"] = '\t'


def run():
    '''
	le = label_encoder()
	ne = num_encoder(offset=5)
	a = ['a','b','c']
	le.fit(a)
	b = le.transform(['c'])
	ne.fit(a,4)
	c = ne.transform('a')
	'''

    train_config, test_config = get_config()
    check_config(train_config)
    check_config(test_config)

    # gen train
    all_encoder = progress.pure_readlines(train_config)

    # gen test
    progress.pure_readlines(test_config)
    progress.gen_all_pairs(test_config, all_encoder)


if __name__ == '__main__':
    run()
