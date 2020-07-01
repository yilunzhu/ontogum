import io, os, sys
from collections import defaultdict
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
        self.child_cop = bool()


def coref_(fields: list) -> dict:
    """
    find the coref relations between the current entity and next entity
    example: 15-8[81_3]
    :param fields: elements in a line
    """
    coref = {}
    # when the entity has not coref relations except that it is pointed to by other entities
    if fields[-1] != '_':
        coref_types = fields[-2].split('|')
        for i, x in enumerate(fields[-1].split('|')):
            point_to = x.split('[')[0]
            cur_e = ''
            next_e = ''
            coref_type = ''
            if ']' in x:
                e_info = x.strip(']').split('[')[1].split('_')
                cur_e = e_info[1] if e_info[1] != '0' else ''
                next_e = e_info[0]
                if next_e == '0':
                    next_e = f'0_{point_to}'

                coref_type = coref_types[i]

            # e.g. 7-3	397-403	people	person	new	ana	8-7
            elif fields[-2] != '_':
                coref_type = coref_types[i]

            coref[cur_e] = (point_to, next_e, coref_type)

    return coref


def add_tsv(entities: dict, fields: list, coref_r: dict, doc: dict, entity_group: list, antecedent_dict):
    """
    add entities (unique id) in the current line to the doc
    :param entities: entity id and type
    :param fields: elements in a line
    :param coref_r: coref relations
    :param doc: coref in an article
    """
    for id, e in entities.items():
        text_id = fields[0]
        k = id

        if k in doc.keys(): # if the named entity id is more than one word, add to the existed id
            doc[k].tok += f" {fields[2]}"
            doc[k].span_len += 1

        else:   # if the word is B-NE (e.g. B-PER) of the named entity, create a new Coref class
            if k in coref_r.keys() or '' in coref_r.keys():
                if_fake = True if '' in coref_r.keys() else False   # if the NE does not have id, create a fake id
                new_id = f'0_{text_id}' if if_fake else k
                if f'0_{text_id}' in doc.keys():
                    del doc[new_id]

                doc[new_id] = Coref()
                doc[new_id].text_id = text_id
                doc[new_id].tok = fields[2]
                doc[new_id].e_type = e
                doc[new_id].cur = new_id
                doc[new_id].coref = coref_r[id][0]

                # if the coref does not a named entity
                # 7-3	397-403	people	person	new	ana	8-7
                # 8-7	472-476	they	person	giv	coref	9-9
                if coref_r[id][1] == '' and coref_r[id][0]:
                    doc[new_id].next = f'0_{coref_r[id][0]}'
                else:
                    doc[new_id].next = coref_r[id][1]

                doc[new_id].coref_type = coref_r[id][2]

                next_e = coref_r[id][1]

                # if the coref.next is not a named entity, create a fake entity id
                if (coref_r[id][1] == '0' or coref_r[id][1] == ''):
                    next_e = f'0_{coref_r[id][0]}'
                    if f'0_{coref_r[id][0]}' not in doc.keys():
                        fake_id = next_e
                        doc[fake_id] = Coref()
                        doc[fake_id].text_id = coref_r[id][0]

                # combine coref entities in group
                if_new_group = True
                for idx, g in enumerate(entity_group):
                    if new_id in g:
                        if_new_group = False
                        entity_group[idx].append(next_e)
                        break
                    if next_e in g:
                        if_new_group = False
                        entity_group[idx].append(new_id)
                if if_new_group:
                    entity_group.append([new_id, next_e])

                # antecedent info
                antecedent_dict[new_id] = next_e

            # if the current line does not have coref but it's the coref of the previous entity, add token info
            elif f'0_{text_id}' in doc.keys():
                fake_id = f'0_{text_id}'
                doc[fake_id].etype = e
                doc[fake_id].tok = fields[2]

            # if no next coref, but has antecedent
            elif k in antecedent_dict.values():
                doc[k] = Coref()
                doc[k].text_id = text_id
                doc[k].tok = fields[2]
                doc[k].e_type = e
                doc[k].cur = id
                doc[k].coref = ''
                doc[k].next = ''
                doc[k].coref_type = ''

    return entity_group, antecedent_dict


def break_dep_doc(doc):
    sent_id = 0
    sents = defaultdict(list)
    for i, line in enumerate(doc):
        if line[0].startswith('# sent_id'):
            sent_id += 1
        elif len(line) > 1 and not line[0].startswith('#'):
            sents[sent_id].append(line)
    return sents


def check_dep_cop_child(sent: list, head_range: list, head_id: str) -> bool:
    # head_range = [int(x) for x in head_range]
    for row in sent:
        if row[0] not in head_range and row[6] == head_id and row[7] == 'cop':
            return True
    return False


def process_doc(dep_doc, coref_doc):
    """
    align dep lines in conllu and coref lines in tsv, extract coref-related information for each entity id
    """
    doc = {}
    antecedent_dict = {}
    entity_group = [[]]
    tokens = []

    for coref_line in coref_doc:
        if coref_line.startswith('#'):
            continue
        elif coref_line:
            coref_fields = coref_line.strip().split('\t')
            line_id, token = coref_fields[0], coref_fields[2]

            # test
            if coref_fields[0] == '9-12':
                a = 1

            if coref_fields[3] == '_' and coref_fields[4] == '_':
                tokens.append((token, line_id, [], {}))
                continue

            # entity info
            entities = {'' if '[' not in x else x.strip(']').split('[')[1]: x.split('[')[0]
                        for x in coref_fields[3].split('|')}

            # coref info
            coref = coref_(coref_fields)
            tokens.append((token, line_id, list(entities.keys()), coref))

            # tsv
            add_tsv(entities, coref_fields, coref, doc, entity_group, antecedent_dict)

    # map text_id and entity
    id_e = {v.text_id: (v.span_len, k) for k,v in doc.items()}

    # break the dep conllu into sents
    dep_sents = break_dep_doc(dep_doc)

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
            if dep_text_id == '15-21':
                a = 1
            if dep_text_id in id_e:
                span_len, entity = id_e[dep_text_id][0], id_e[dep_text_id][1]

                # find dep information and index for each word in heads
                heads = [dep_doc[x] for x in range(int(i), int(i)+span_len) if len(dep_doc[x]) == 10]
                head_range = [dep_doc[x][0] for x in range(int(i), int(i)+span_len) if len(dep_doc[x]) == 10]

                # loop each word in the head to find the head_func/head_pos/if_cop_in_dep for the entity
                for row in heads:
                    # if find the ROOT
                    if row[6] == '0':
                        doc[entity].head = row[1]
                        doc[entity].lemma = row[2]
                        doc[entity].head_func = row[7]
                        doc[entity].head_pos = row[4]
                        # check if the head has a copula child
                        doc[entity].child_cop = check_dep_cop_child(dep_sents[dep_sent_id], head_range, row[0])

                    # if the head is outside the range, it's the head of the entity
                    elif doc[entity].head_func == '' and row[6] not in head_range:
                        doc[entity].head = row[1]
                        doc[entity].lemma = row[2]
                        doc[entity].head_func = row[7]
                        doc[entity].head_pos = row[4]
                        doc[entity].child_cop = check_dep_cop_child(dep_sents[dep_sent_id], head_range, row[0])
                    doc[entity].func += f' {row[7]}'
                    doc[entity].pos += f' {row[4]}'
                doc[entity].func = doc[entity].func.strip()
                doc[entity].pos = doc[entity].pos.strip()

                if doc[entity].head_func == '':
                    raise ValueError('The head feature is empty.')

    # group dict
    entity_group = [x for x in entity_group if x]
    group_id = 0
    group_dict = {}
    for lst in entity_group:
        group_id += 1
        for x in lst:
            group_dict[x] = group_id

    return doc, tokens, group_dict, antecedent_dict
