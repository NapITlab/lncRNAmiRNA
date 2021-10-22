import datetime
import json
import logging
import os
import sys
import time
import traceback

import pandas as pd
from django.conf import settings
from rest_framework.response import Response

logger = logging.getLogger("lncRNAmiRNA_model")
telegram_logger = logging.getLogger("lncRNAmiRNA_model.telegram")


def run_or_cached(fp: str, func, args: list, kwargs: dict):
    """
    if cached get function output from cache
    :param fp: filepath to cached file
    :param func: func to run if not cached
    :param args: func args
    :param kwargs: func kwargs
    :return:
    """
    error_msg = f"Cache for extension of file '{fp}' is not implemented"

    if not os.path.isfile(fp) or not settings.CACHE_FILES:
        to_return = func(*args, **kwargs)

        if settings.CACHE_FILES:
            if fp.endswith(".json"):
                with open(fp, "w") as json_f:
                    json.dump(to_return, json_f)
            elif fp.endswith(".csv"):
                to_return.to_csv(fp, index=False)
            else:
                raise NotImplementedError(error_msg)
    else:
        logger.debug(f"Skipped run of '{func.__name__}', using cached results from '{fp}'")
        if fp.endswith(".json"):
            with open(fp, "r") as json_f:
                to_return = json.load(json_f)
        elif fp.endswith(".csv"):
            to_return = pd.read_csv(fp)
        else:
            raise NotImplementedError(error_msg)

    return to_return


def csv_to_fasta(csv_fp: str, fasta_fp: str):
    csv = pd.read_csv(csv_fp, header=0)

    with open(fasta_fp, "w") as fasta:
        for i, row in csv.iterrows():
        # seq_len = len(row['Sequence'])
        # fasta_fp_len = fast_fp_prefix + "_" + str(seq_len) + ".fasta"

            fasta.write(f">{i}_{row['gene']}\n{row['Sequence']}\n")


def create_timestamp(historical_moment: str, beginning: float):
    ts = time.time()
    logger.debug(f"{historical_moment} elapsed: {datetime.timedelta(seconds=ts-beginning)}")
    return ts


def make_error_msg(what):
    ex_type, ex_value, ex_trace = sys.exc_info()
    traceback_str = traceback.format_exc()

    return ex_value, traceback_str, f"{what} failed:\n" \
                     f"ex_type: {ex_type}\n" \
                     f"ex_value: {ex_value}\n" \
                     f"trace: {traceback_str}"


def ErrorResponse(request, traceback, message, error_status):
    url = ''
    try:
        url = request.stream.path
    except Exception as ex:
        pass
    log = "user: {}\nurl: {}\nmessage: {}\ntraceback: {}".format(request.user.username, url, message, traceback)

    telegram_logger.error(log)
    logger.error(log)
    return Response({'message': message}, status=error_status)
