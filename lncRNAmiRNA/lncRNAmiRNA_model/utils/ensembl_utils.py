import logging

from ensemblrest import EnsemblRest

logger = logging.getLogger("lncRNAmiRNA_model")


ensRest = EnsemblRest()


def get_ens_seq(ens_id):
    return ensRest.getSequenceById(id=ens_id, type="cdna")["seq"]
