import io, os, sys
import pandas as pd
import numpy as np
from argparse import ArgumentParser


class Coref(object):
    """
    the class of coref units (span mentions), each mention contains text id, tokens, entity types, current coref,
    next coref, coref type (coref or bridging), head dep function, head pos tag, span's dep functions,
    span's pos tags, span length
    """
    def __init__(self):
        self.text_id = str()
        self.tok = str()
        self.e_type = str()
        self.cur = str()
        self.next = str()
        self.coref = {}
        self.coref_type = str()
        self.head_func = str()
        self.head_pos = str()
        self.func = str()
        self.pos = str()
        self.span_len = 1


def coref_(fields: list) -> dict:
    """
    find the coref relations between the current entity and next entity
    example: 15-8[81_3]
    :param fields: elements in a line
    """
    coref = {}
    if fields[-1] != '_':
        for x in fields[-1].split('|'):
            point_to = x.split('[')[0]
            cur_e = ''
            next_e = ''
            if ']' in x:
                e_info = x.strip(']').split('[')[1].split('_')
                cur_e = e_info[1]
                next_e = e_info[0]
            coref[cur_e] = (point_to, next_e)
    return coref


def add_doc(entities: dict, fields: list, coref: dict, doc: dict):
    """
    add entities (unique id) in the current line to the doc
    :param entities: entity id and type
    :param fields: elements in a line
    :param coref: coref relations
    :param doc: coref in an article
    """
    for id, e in entities.items():
        text_id = fields[0]
        k = id
        if k in doc.keys():
            doc[k].tok += f" {fields[2]}"
            doc[k].span_len += 1
        else:
            if k in coref.keys():
                doc[k] = Coref()
                doc[k].text_id = text_id
                doc[k].tok = fields[2]
                doc[k].e_type = e
                if len(entities) == 1 and len(coref) == 1 and '-1' in coref.keys():
                    doc[k].coref = coref['-1'][0]
                    doc[k].next = coref['-1'][1]
                else:
                    doc[k].coref = coref[id][0]
                    doc[k].next = coref[id][1]


def process_doc(dep_doc, coref_doc) -> dict:
    """
    align dep lines in conllu and coref lines in tsv, extract coref-related information for each entity id
    """
    doc = {}

    for coref_line in coref_doc:
        if coref_line.startswith('#'):
            continue
        elif coref_line:
            coref_fields = coref_line.strip().split('\t')
            if coref_fields[3] == '_' and coref_fields[4] == '_':
                continue

            # entity info
            entities = {-1 if '[' not in x else x.strip(']').split('[')[1]: x.split('[')[0]
                        for x in coref_fields[3].split('|')}

            # coref info
            coref = coref_(coref_fields)

            # tsv
            add_doc(entities, coref_fields, coref, doc)

    # map text_id and entity
    id_e = {v.text_id: (v.span_len, k) for k,v in doc.items()}

    # dep
    dep_sent_id = 0
    for i, dep_line in enumerate(dep_doc):
        if dep_line[0].startswith('# sent_id'):
            dep_sent_id += 1
        elif dep_line[0].startswith('#'):
            continue
        elif len(dep_line) > 1:
            # match dep_text_id to the format in coref tsv
            dep_text_id = f'{dep_sent_id}-{dep_line[0]}'
            if dep_text_id in id_e:
                span_len, entity = id_e[dep_text_id][0], id_e[dep_text_id][1]
                if span_len == 1:
                    doc[entity].head_func = dep_line[7]
                    doc[entity].head_pos = dep_line[4]
                    doc[entity].func = dep_line[7]
                    doc[entity].pos = dep_line[4]
                else:
                    heads = [dep_doc[x] for x in range(int(i), int(i)+span_len)]
                    head_range = [dep_doc[x][0] for x in range(int(i), int(i)+span_len)]
                    for row in heads:
                        if row[6] == '0':
                            doc[entity].head_func = row[7]
                            doc[entity].head_pos = row[4]
                        # if the head is outside the range, it's the head of the entity
                        elif row[6] not in head_range:
                            doc[entity].head_func = row[7]
                            doc[entity].head_pos = row[4]
                        doc[entity].func += f' {row[7]}'
                        doc[entity].pos += f' {row[4]}'
                    doc[entity].func = doc[entity].func.strip()
                    doc[entity].pos = doc[entity].pos.strip()

                    if doc[entity].head_func == '':
                        raise ValueError('The head feature is empty.')

    return doc


# if __name__ == '__main__':
#     parser = ArgumentParser()
#     parser.add_argument('--dep', default=os.path.join('gum', 'dep', 'ud'), help='Path to the gum/dep/ud directory')
#     parser.add_argument('--coref', default=os.path.join('gum', 'coref', 'tsv'), help='Path to the gum/coref/tsv directory')
#     args = parser.parse_args()
#
#     dep_dir = args.dep
#     coref_dir = args.coref
#
#     readDir(dep_dir, coref_dir)
