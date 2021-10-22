import logging
import os
import shutil
import subprocess
import sys

import numpy as np
import pandas as pd
from django.conf import settings

logger = logging.getLogger("lncRNAmiRNA_model")
NP_AR_DTYPE = np.float32


def get_pairs(path_file_coord):
    with open(path_file_coord, "r") as text_file:
        text = text_file.read()

    pairs_txt = text.split('/pairs')[1].split('def')[0]

    pairs = [
        pair[1:-1].split(' ')
        for pair in pairs_txt.split('\n')[1:-1]
    ]
    return pairs


def get_probs(path_file_prob):
    with open(path_file_prob, "r") as text_file:
        text = text_file.read()

    pair_probs = text.split('%start of base pair probability data\n')[1]\
        .split('\nshowpage')[0]\
        .split("\n")
    return pair_probs


def pairs_read(path_file, seq_len):
    pairs = get_pairs(path_file)

    paired = np.zeros(seq_len, dtype=NP_AR_DTYPE)

    for pair in pairs:
        f = int(pair[0]) - 1  # 0-based
        s = int(pair[1]) - 1  # 0-based
        paired[f] = True
        paired[s] = True

    return paired


def probs_read(path_file, seq_len):

    pairs = get_probs(path_file)

    max_probs = np.zeros(seq_len, dtype=NP_AR_DTYPE)

    for pair in pairs:
        pair = pair.split(" ")
        f = int(pair[0]) - 1
        s = int(pair[1]) - 1
        prob = float(pair[2])

        if max_probs[f] < prob:
            max_probs[f] = prob

        if max_probs[s] < prob:
            max_probs[s] = prob

    return max_probs


def seq2struct(mrna):
    """
    2D структура mRNA:
    parallel --lb --jobs 48 --plus --quote --header : --colsep '\t' --verbose \
        --joblog $LogsFolder/paralelllog_RNAfold.txt \
        --tmpdir $tmpdir \
        --compress \
        RNAfold \
        -p \
        -d2 \
        --id-prefix={gene_name} \
        -i {file_in}.fa \
        :::: $FastaFilesTable \
        2>&1 | tee $LogsFolder/consolelog_RNAfold.txt
    :return:
    """
    logger.debug(f"seq2struct for '{mrna['id']}' started")

    tmp_folder = os.path.join(settings.TMP_DIR, settings.RNA_FOLD_TMP_DIR, mrna["id"])

    if not os.path.exists(tmp_folder):
        os.makedirs(tmp_folder)

    cwd = os.getcwd()
    os.chdir(tmp_folder)

    try:
        path_file_coord = f"{mrna['id']}_0001_ss.ps"
        path_file_prob = f"{mrna['id']}_0001_dp.ps"

        if not (os.path.isfile(path_file_coord) and os.path.isfile(path_file_prob)):
            tmp_fa_fn = f"{mrna['id']}.fa"

            with open(tmp_fa_fn, "w") as tmp_fa:
                tmp_fa.write(f">{mrna['id']}\n")
                tmp_fa.write(mrna["seq"])

            cmd = [settings.RNA_FOLD_EXE, "-p", "-d2", f"--id-prefix={mrna['id']}", "-i", tmp_fa_fn]

            proc = subprocess.Popen(cmd)
            ret_code = proc.wait()

            if ret_code != 0:
                raise Exception(f"RNAfold return code != 0: cmd:\n {' '.join(cmd)}")

        logger.debug(f"seq2struct for '{mrna['id']}' ended")

        pairs = pairs_read(path_file_coord, mrna["len"])
        probs = probs_read(path_file_prob, mrna["len"])

        return pairs, probs

    except Exception:
        ex_type, ex_value, ex_trace = sys.exc_info()
        ex_msg = f"2D structure for mRna '{mrna['id']}' failed"
        raise ex_type(ex_msg).with_traceback(ex_trace)
    finally:
        os.chdir(cwd)
        if settings.CLEAR_TMP:
            shutil.rmtree(tmp_folder)


def coordinate_nucleotide_read_legacy(path_file):
    text_file = open(path_file, "r")
    seq = text_file.readlines()
    seq = '\n'.join(seq)
    text_file.close()

    coord = seq.split('/coor')[1].split('pairs')[0]

    coord = pd.DataFrame([(i.replace('[', '').replace(']', '').split(' ')) for i in coord.split('\n\n')[1:]])

    coord = coord[(coord[0] != '') & (coord[0] != '/') & (coord[0] != '/arcs')]

    coord[0] = coord[0].astype('float')
    coord[1] = coord[1].astype('float')

    pair = seq.split('/pairs')[1].split('def')[0]

    pair = pd.DataFrame([(i.replace('[', '').replace(']', '').split(' ')) for i in pair.split('\n\n')[1:]])

    pair = pair[(pair[0] != '')]

    pair[0] = pair[0].astype('int')
    pair[1] = pair[1].astype('int')

    pair_list = list(pair[0]) + list(pair[1])

    sequence = seq.split('sequence { (\\\n\n')[1].split(') } def\n')[0].replace('\n', '').replace('\\', '')

    data = pd.DataFrame(list(sequence))

    data['coord_x'] = coord[0]
    data['coord_y'] = coord[1]

    data['ind'] = data.index

    data['pair'] = data['ind'].apply(lambda p: (p + 1) in pair_list)

    return data[['ind', 'pair']]


def probability_read_legacy(path_file):
    text_file = open(path_file, "r")
    seq = text_file.readlines()
    seq = '\n'.join(seq)
    text_file.close()

    len_seq = len((seq.split('sequence { (\\\n\n')[1]).split('\\\n\n) }')[0].replace('\\\n\n', ''))

    base_pair = (seq.split('%start of base pair probability data\n\n')[1].split('\nshowpage')[0])
    base_pair = base_pair.replace('lbox', 'ubox').split(' ubox\n\n')

    base_pair = pd.DataFrame([i.split(' ')[:3] for i in base_pair], columns=('n1', 'n2', 'prob'))

    base_pair1 = base_pair.copy()
    base_pair2 = base_pair.copy()

    base_pair1['n'] = base_pair1['n1']
    base_pair2['n'] = base_pair1['n2']

    base_pair = base_pair1[['n', 'prob']].append(base_pair2[['n', 'prob']])
    base_pair = base_pair.groupby(by=['n'], as_index=False).agg({'prob': 'max'})

    base_pair.columns = ['ind', 'max_prob']

    return base_pair


def parser_2D_structure_mRNA_legacy(path_file_coord, path_file_prob):
    data_coord = coordinate_nucleotide_read_legacy(path_file_coord)
    data_prob = probability_read_legacy(path_file_prob)

    data_coord['ind'] = data_coord['ind'].astype('int')
    data_prob['ind'] = data_prob['ind'].astype('int')

    data = pd.merge(data_coord, data_prob, on=['ind'], how="left").fillna(0)

    return data


def seq2struct_legacy(mrna):
    """
    2D структура mRNA:
    parallel --lb --jobs 48 --plus --quote --header : --colsep '\t' --verbose \
        --joblog $LogsFolder/paralelllog_RNAfold.txt \
        --tmpdir $tmpdir \
        --compress \
        RNAfold \
        -p \
        -d2 \
        --id-prefix={gene_name} \
        -i {file_in}.fa \
        :::: $FastaFilesTable \
        2>&1 | tee $LogsFolder/consolelog_RNAfold.txt
    :return:
    """
    logger.debug(f"seq2struct_legacy for '{mrna['id']}' started")

    tmp_folder = os.path.join(settings.TMP_DIR, settings.RNA_FOLD_TMP_DIR, mrna["id"])

    if not os.path.exists(tmp_folder):
        os.makedirs(tmp_folder)

    cwd = os.getcwd()
    os.chdir(tmp_folder)

    try:
        path_file_coord = f"{mrna['id']}_0001_ss.ps"
        path_file_prob = f"{mrna['id']}_0001_dp.ps"

        if not (os.path.isfile(path_file_coord) and os.path.isfile(path_file_prob)):
            tmp_fa_fn = f"{mrna['id']}.fa"

            with open(tmp_fa_fn, "w") as tmp_fa:
                tmp_fa.write(f">{mrna['id']}\n")
                tmp_fa.write(mrna["seq"])

            cmd = [settings.RNA_FOLD_EXE, "-p", "-d2", f"--id-prefix={mrna['id']}", "-i", tmp_fa_fn]

            proc = subprocess.Popen(cmd)
            ret_code = proc.wait()

            if ret_code != 0:
                raise Exception(f"RNAfold return code != 0: cmd:\n {' '.join(cmd)}")

        logger.debug(f"seq2struct_legacy for '{mrna['id']}' ended")

        return parser_2D_structure_mRNA_legacy(path_file_coord, path_file_prob)

    except Exception:
        ex_type, ex_value, ex_trace = sys.exc_info()
        ex_msg = f"2D structure for mRna '{mrna['id']}' failed"
        raise ex_type(ex_msg).with_traceback(ex_trace)
    finally:
        os.chdir(cwd)
        if settings.CLEAR_TMP:
            shutil.rmtree(tmp_folder)


def shrna_structure_test(path_file_coord: str, path_file_prob: str) -> bool:
    """
    path_file_coord = f"{mrna['id']}_0001_ss.ps"
    path_file_prob = f"{mrna['id']}_0001_dp.ps"
    """

    # probs
    probs = get_probs(path_file_prob)
    probs_dict = {}
    for pair in probs:
        pair = pair.split(" ")
        f = int(pair[0]) - 1
        s = int(pair[1]) - 1
        prob = float(pair[2])

        if f not in probs_dict:
            probs_dict[f] = {}
        if s not in probs_dict:
            probs_dict[s] = {}

        probs_dict[f][s] = prob
        probs_dict[s][f] = prob

    # pairs
    pairs = get_pairs(path_file_coord)

    # let's check if there is with high probability paired subsequence of length at least PAIRED_LEN
    PROB_THRESHOLD = 0.9

    high_paired = []

    for pair in pairs:
        f = int(pair[0]) - 1  # 0-based
        s = int(pair[1]) - 1  # 0-based

        if probs_dict[f][s] > PROB_THRESHOLD:
            if f > s:
                high_paired.append((s,f))
            else:
                high_paired.append((f, s))

    high_paired.sort(key=lambda x: x[0])

    PAIRED_LEN = 21
    sub_len = 0
    start = -2
    end = -2
    for high_pair in high_paired:
        if high_pair[0] - start == 1 and end - high_pair[1] == 1:
            sub_len += 1
            if sub_len == PAIRED_LEN:
                return True
        else:
            sub_len = 1

        start = high_pair[0]
        end = high_pair[1]

    logger.warning(f"Files '{path_file_coord}' and '{path_file_prob}' contain suspicious shRNA")
    return False
