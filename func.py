import io, os
from copy import deepcopy
from process_data import Coref


class Convert(object):
    def __init__(self, doc: dict, antecedent_dict, group_dict, if_appos, if_singletons):
        self.antecedent_dict = antecedent_dict
        self.group_dict = group_dict
        self.doc = doc
        self.if_appos = if_appos
        self.if_singletons = if_singletons

    def _remove_junk(self):
        if '0_' in self.doc.keys():
            del self.doc['0_']

    def _expand_acl(self):
        """
        If the acl contains a coref, expand the span to its head if the head does not indicate a span
        :return: update self.docs

        to restore the conll: '\n'.join(['\t'.join(x) for x in doc[i]])
        """
        loop_doc = deepcopy(self.doc)
        for k, _coref in loop_doc.items():
            sent_id = self.doc[k].text_id.split('-')[0]
            if _coref.acl_children and not _coref.expanded:
                if k.startswith('0_'):  # if the original entity has only one token, create a new fake id to handle the expanded acl

                    # create a new fake id
                    new_k = str(self.last_e + 1)
                    self.last_e += 1
                    self.doc[new_k] = deepcopy(self.doc[k])
                    self.doc[new_k].cur = new_k

                    # find prev
                    for prev, prev_coref in self.doc.items():
                        if prev_coref.next and prev_coref.next == k:
                            self.doc[prev].next = new_k
                            break

                    # reset the original k
                    self.doc[k] = Coref()
                    self.doc[k].delete = True

                    # update new_id2entity
                    cur_id = self.doc[new_k].text_id
                    ori_e = k.split('_')[-1]
                    ids = [f'{sent_id}-{tok_id}' for tok_id in self.doc[new_k].acl_children] + [cur_id]

                    # update last_e
                    self.last_e += 1

                else:
                    new_k = k
                    cur_id = self.doc[new_k].text_id
                    ori_e = k.split('_')[-1]
                    ids = [f'{sent_id}-{tok_id}' for tok_id in self.doc[new_k].acl_children] + [cur_id]

                # find the beginning id of the entity
                '''
                Sometimes the acl span precedes the entity
                - Example:
                    1	Born	bear	VERB	VBN	Tense=Past|VerbForm=Part	5	acl	_	_
                    2	in  in	ADP	IN	_	3	case	_	_
                    3	England	England	PROPN	NNP	Number=Sing	1	obl	_	Entity=(place-12)|SpaceAfter=No
                    4	,	,	PUNCT	,	_	1	punct	_	_
                    5	Norton	Norton	PROPN	NNP	Number=Sing	6	nsubj	_	Entity=(person-1)
                '''
                min_id = min([int(x.split('-')[-1]) for x in ids])
                if f'{sent_id}-{min_id}' != self.doc[new_k].text_id:
                    self.doc[new_k].text_id = f'{sent_id}-{min_id}'

                for id in ids:
                    if id in self.new_id2entity.keys():
                        if ori_e in self.new_id2entity[id]:
                            self.new_id2entity[id] = [new_k if i == ori_e else i for i in self.new_id2entity[id]]
                        else:
                            self.new_id2entity[id].append(new_k)
                    else:
                        self.new_id2entity[id] = [new_k]
                cur_span = [str(int(self.doc[new_k].text_id.split('-')[-1]) + x) for x in
                            range(self.doc[new_k].span_len)]
                self.doc[new_k].span_len += len([x for x in _coref.acl_children if x not in cur_span])

    def _verb_contract(self):
        """
        Contract the verbal markables to the verbs

        example:
            [I want to go to Rome.] [This] angered Kim.  -> ON: [want]
            I want [to go to Rome]. Kim wants to do [that] too. -> ON: [go]
        """
        loop_doc = deepcopy(self.doc)
        for k, _coref in loop_doc.items():
            if _coref.verb_head_aux:
                kept, kept_head = _coref.verb_head_aux
            elif _coref.verb_head:
                kept, kept_head = _coref.verb_head, _coref.head_id
            else:
                kept, kept_head = False, ''

            if k in self.doc.keys() and kept and _coref.next in self.doc.keys() and _coref.next != '':

                # (1) redirect the current markable and (2) create a new id to shorten the markable span
                new_id = str(self.last_e + 1)
                self.last_e += 1

                self.doc[new_id] = deepcopy(_coref)
                self.doc[new_id].cur = new_id
                self.doc[new_id].span_len = 1
                self.doc[new_id].text_id = kept_head
                self.doc[new_id].tok = ''
                if kept_head not in self.new_id2entity.keys():
                    self.new_id2entity[kept_head] = []
                self.new_id2entity[kept_head].append(new_id)

                # modify the antecedent
                for prev_k, prev_v in loop_doc.items():
                    if prev_k in self.doc.keys() and prev_v.next == k:
                        self.doc[prev_k].next = new_id

                # delete the original markable
                self.doc[k].delete = True

    def _remove_compound(self):
        """
        if the func is 'compound' and (1) not NNP/NNPS, (2) has coref, remove the current coref relation
            # if the current coref relation has previous and next coref, connect the two

        example: Allergan Inc. said it received approval to sell the PhacoFlex
                intraocular lens, the first foldable silicone lens available
                for [cataract surgery]*. The lens' foldability enables it to be
                inserted in smaller incisions than are now possible for
                [cataract surgery]*.
        * means two mention spans are not annotated as coreferences.

        Question: [a collaborative pilot project] ... [this (det) pilot project]
        """
        for k, _coref in self.doc.items():
            # currently remove the question example. To avoid deleting such examples, add another condition
            # "_coref.pos not startswith('det')"
            if 'compound' == _coref.head_func and ('NNP' not in _coref.pos and 'NNPS' not in _coref.pos):

                # find prev and next
                prev_k = ''
                for prev, _prev_coref in self.doc.items():
                    if _prev_coref.next and _prev_coref.next == k:
                        prev_k = prev
                        break
                if prev_k and _coref.next:
                    self.doc[prev_k].next = ''
                    self.doc[prev_k].coref = ''
                    self.doc[prev_k].coref_type = ''

                self.doc[k] = Coref()
                self.doc[k].delete = True

    def _remove_bridge(self):
        """
        if the coref type contains "bridge" (also include "bridge:aggr"), remove that coref relation
        """
        for k, _coref in self.doc.items():
            if 'bridge' in _coref.coref_type:
                self.doc[k].coref = ''
                self.doc[k].next = ''
                self.doc[k].coref_type = ''

    def _remove_cop(self):
        """
        if (1) two coref mentions are in the same sentence, (2) a copula dep func is the child of the first one,
        remove the coref relations between the two and move the second coref to the first one

        A -> B & B -> C ====> A -> C
        remove B
        Also, the function should handle multiple copula, e.g. copula in coordination
        Example: [He] was [one of the first opponents of the Vietnam War] , and is [a self-described Libertarian Socialist] .
        """
        for k, _coref in self.doc.items():
            # A -> B1..B2 -> C
            # remove B1, B2, ... Bn
            cur_v = deepcopy(self.doc[k])
            while cur_v.head_func != '' and cur_v.next in self.doc.keys() and self.doc[cur_v.next].child_cop == True:
                cur_v = deepcopy(self.doc[cur_v.next])

                self.doc[cur_v.cur].coref = ''
                self.doc[cur_v.cur].next = ''
                self.doc[cur_v.cur].coref_type = ''

                if cur_v.next:
                    self.doc[k].coref = cur_v.coref
                    self.doc[k].next = cur_v.next
                    self.doc[k].coref_type = cur_v.coref_type
                else:
                    self.doc[k].coref = ''
                    self.doc[k].next = ''
                    self.doc[k].coref_type = ''

                self.doc[cur_v.cur] = Coref()
                self.doc[cur_v.cur].delete = True


    def _break_chain(self):
        """
        If two mentions do not obey the specificity scale, break the coref chain

        simple way to break currently:
        the > a

        """
        for k, _coref in self.doc.items():
            if _coref.appos:
                continue
            if _coref.next and _coref.next != '0' and _coref.next in self.doc.keys() and self.doc[_coref.next].definite == False:
                if _coref.proper:   # do not separate the chain when the antecedent is a proper noun
                    continue
                """
                WARNING: This is not a 100% correct operation but avoids some annotation errors
                """
                # If the chain's next is a definite entity and there are in the same sentence, do not break the chain
                next_next = deepcopy(self.doc[_coref.next].next)
                if next_next and (self.doc[next_next].lemma in ['he', 'she'] or self.doc[next_next].pos == 'NNP'):
                    next_sent_id = self.doc[_coref.next].text_id.split('-')[0]
                    next_next_sent_id = self.doc[next_next].text_id.split('-')[0]
                    if int(next_next_sent_id) <= int(next_sent_id) + 2:
                        print(f'Warning: Skip breaking chains in Line {next_sent_id}.')
                        continue

                break_group = max(self.group_dict.values()) + 1
                next_coref = self.doc[_coref.next]
                while next_coref.cur in self.antecedent_dict.keys():
                    # avoid cataphora that the coref points to itself
                    # E.g. GUM_fiction_pag
                    #      55-1	3945-3954	Something	person	giv	cata	55-1
                    if next_coref.text_id == next_coref.next or f'0_{next_coref.text_id}' == next_coref.next:
                        break

                    self.group_dict[self.doc[next_coref.cur].cur] = break_group

                    # it is a repeated operation, but help with the last coref, which will not appear in the antecedent_dict.keys()
                    # if self.doc[next_coref.next].cur in self.group_dict.keys():
                    if next_coref.next in self.doc.keys():
                        self.group_dict[self.doc[next_coref.next].cur] = break_group
                        next_coref = self.doc[next_coref.next]
                    else:
                        break

                self.doc[k].coref = ''
                self.doc[k].next = ''
                self.doc[k].coref_type = ''

                # break the coref chain between cur and next
                if k in self.antecedent_dict.keys():
                    del self.antecedent_dict[k]

    def _appos_merge(self):
        """
        If coref_type==appos, merge the appos into the current coref

        Example:
            from :
                27-40	3795-3798	the	object[220]	new[220]	appos	27-42[0_220]
                27-41	3799-3803	13th	object[220]	new[220]	_	_
                27-42	3804-3812	Benjamin	object	giv	coref	27-45[221_0]
            to:
                27-40	3795-3798	the	object[220]|object[999]	new[220]|new[999]	coref|appos	27-45[221_220]|27-42[0_999]
                27-41	3799-3803	13th	object[220]|object[999]	new[220]|new[999]	_	_
                27-42	3804-3812	Benjamin	object||object[220]	giv|new[220]	_	_
        """
        loop_doc = deepcopy(self.doc)
        for k1, v in loop_doc.items():
            k1_sent_id = v.text_id.split('-')[0]
            for k2, next_v in loop_doc.items():
                if v.delete or next_v.delete:
                    continue
                # assign the appos value to be True if it is missed in the earlier step
                # (the missing may be due to that "coref_type" does not correlate with "appos")

                k2_sent_id = next_v.text_id.split('-')[0]
                if k1_sent_id == k2_sent_id and v.next == k2 and v.coref_type == 'appos':
                    self.doc[k1].appos = True
                    k1_tok_start_id = int(v.text_id.split('-')[-1])

                    prev_start = int(v.text_id.split('-')[-1])
                    prev_last = int(v.text_id.split('-')[-1]) + v.span_len - 1
                    next_start = int(next_v.text_id.split('-')[-1])
                    next_last = int(next_v.text_id.split('-')[-1]) + next_v.span_len - 1

                    # search the antecedent of k1
                    ante = ''
                    for ante_k, ante_v in self.doc.items():
                        if ante_v.next and ante_v.next in self.doc.keys() and ante_v.next == k1:
                            ante = ante_k
                            break

                    # create a new e as the new big span for the apposition
                    new_k1 = str(self.last_e+1)
                    self.last_e += 1
                    self.doc[new_k1] = deepcopy(self.doc[k1])
                    self.doc[new_k1].cur = new_k1
                    self.doc[new_k1].coref = next_v.coref
                    self.doc[new_k1].next = next_v.next
                    self.doc[new_k1].coref_type = next_v.coref_type
                    self.doc[new_k1].e_type = v.e_type
                    self.doc[new_k1].new_e = True

                    if prev_last <= next_last:
                        self.doc[new_k1].func += ' ' + next_v.func
                        self.doc[new_k1].pos += ' ' + next_v.pos
                        self.doc[new_k1].tok += ' ' + next_v.tok

                    self.last_e += 1

                    self.doc[k1].dep_appos = True
                    # self.doc[k1].appos_point_to = new_k1

                    # add k1 span to new_k1
                    k1_span = [f'{k1_sent_id}-{i}' for i in range(prev_start, prev_last+1)]
                    for i in k1_span:
                        if i not in self.new_id2entity.keys():
                            self.new_id2entity[i] = []
                        self.new_id2entity[i].append(new_k1)

                    # fill the gap
                    gap = [f'{k1_sent_id}-{i}' for i in range(prev_last+1, next_start)]
                    next_span_len = 0 if prev_last > next_last else next_v.span_len
                    self.doc[new_k1].span_len += next_span_len + len(gap)
                    for i in gap:
                        # self.doc[new_k1].tok += f' {i}'
                        if i not in self.new_id2entity.keys():
                            self.new_id2entity[i] = []
                        self.new_id2entity[i].append(new_k1)

                    # check the token right after the appositive, if it is in '|)|", etc., expand the larger span
                    if next_last <= len(self.doc[k1].sent) - 1 and prev_last <= next_last:
                        next_tok = self.doc[k1].sent[next_last][1]
                        next_tok_id = self.doc[k1].sent[next_last][0]
                        # print(next_tok)
                        if next_tok in ["'", '"', ')', ']', '’', '”', '）', '}']:
                            self.doc[new_k1].span_len += 1
                            self.doc[new_k1].tok += ' ' + next_tok
                            id = f'{k1_sent_id}-{next_tok_id}'
                            if id not in self.new_id2entity.keys():
                                self.new_id2entity[id] = []
                            self.new_id2entity[id].append(new_k1)

                    # check the token between the two markables of the appositive construction, if it is in '|-|",
                    # move it to the second markable
                    prev_tok = self.doc[k1].sent[next_start-1][1]
                    prev_tok_id = int(self.doc[k1].sent[next_start-1][0])
                    id = f'{k1_sent_id}-{prev_tok_id}'
                    if prev_tok in ['"', "'", '-'] and prev_tok_id <= prev_last:
                        print(prev_tok)
                        self.doc[k1].span_len -= 1

                        self.doc[k2].span_len += 1
                        self.doc[k2].tok = prev_tok + ' ' + self.doc[k2].tok
                        if id not in self.new_id2entity.keys():
                            self.new_id2entity[id] = []
                        self.new_id2entity[id].append(k2)

                    # add k2 span to new_k1
                    k2_span = [f'{k1_sent_id}-{i}' for i in range(next_start, next_start+self.doc[k2].span_len)]
                    for i in k2_span:
                        if i not in self.new_id2entity.keys():
                            self.new_id2entity[i] = []
                        self.new_id2entity[i].append(new_k1)

                    if ante:
                        self.doc[ante].next = new_k1

                    # add appos ids to new_k1 if the original k2 has only one token
                    ids = self.doc[new_k1].appos
                    if k2.startswith('0_') and len(ids) > 1:
                        new_k2 = str(self.last_e + 1)
                        self.last_e += 1
                        self.doc[new_k2] = deepcopy(self.doc[k2])
                        self.doc[new_k2].cur = new_k2

                        # points prev
                        self.doc[k1].next = new_k2

                        # reset the original k
                        self.doc[k2] = Coref()
                        self.doc[k2].delete = True

                        # update new_id2entity
                        ori_e = k2.split('_')[-1]
                        for id in ids:
                            if id not in self.new_id2entity.keys():
                                self.new_id2entity[id] = []
                            self.new_id2entity[id].append(new_k2)

                        # update last_e
                        self.last_e += 1
                    else:
                        new_k2 = k2

                    self.doc[new_k2].coref = ''
                    self.doc[new_k2].next = ''
                    self.doc[new_k2].coref_type = ''

                    if not self.if_appos:
                        self.doc[k1].delete = True
                        self.doc[new_k2].delete = True

    def _remove_nested_coref(self):
        for k, _coref in self.doc.items():
            if not _coref.text_id:
                continue
            if self.doc[k].delete:
                continue
            sent_id, tok_id = _coref.text_id.split('-')[0], int(_coref.text_id.split('-')[1])
            ids = [f'{sent_id}-{tok_id+i}' for i in range(_coref.span_len)]
            if self.doc[k].next and self.doc[k].coref in ids:
                next_k = self.doc[k].next
                if self.doc[next_k].next:
                    self.doc[k].next = self.doc[next_k].next
                    self.doc[k].coref = self.doc[next_k].coref
                    self.doc[k].coref_type = self.doc[next_k].coref_type
                else:
                    self.doc[k].next = ''
                    self.doc[k].coref = ''
                    self.doc[k].coref_type = ''

                self.doc[next_k] = Coref()
                self.doc[next_k].delete = True

        # revise the deleted coref
        for del_k, del_coref in self.doc.items():
            if del_coref.next and del_coref.next in self.doc.keys() and self.doc[del_coref.next].delete:
                self.doc[del_k].next = ''
                self.doc[del_k].coref = ''
                self.doc[del_k].coref_type = ''

    def _remove_nmodposs(self):
        """
        Ok, this is wrong. Double check the function to see if this one conflicts with others and why this affects the
        final output.

        Example: [Zurbarán ’s] cycle of Jacob and his Sons
        """
        for k,v in self.doc.items():
            if k in self.doc.keys() and v.next != '' and self.doc[v.next].nmod_poss:
                cur_v = v
                while cur_v.next in self.doc.keys() and cur_v.next != '' and self.doc[cur_v.next].nmod_poss:
                    cur_v = deepcopy(self.doc[cur_v.next])

                    self.doc[cur_v.cur].coref = ''
                    self.doc[cur_v.cur].next = ''
                    self.doc[cur_v.cur].coref_type = ''

            # if k in self.doc.keys() and v.next in self.doc.keys() and v.next != '' and self.doc[v.next].nmod_poss:
                if not cur_v.nmod_poss:
                    self.doc[k].coref = cur_v.coref
                    self.doc[k].coref_type = cur_v.coref_type
                    self.doc[k].next = cur_v.cur
                else:
                    if cur_v.next:
                        self.doc[k].coref = cur_v.coref
                        self.doc[k].coref_type = self.doc[cur_v.next].coref_type
                        self.doc[k].next = cur_v.next
                    else:
                        self.doc[k].coref = ''
                        self.doc[k].coref_type = ''
                        self.doc[k].next = ''


    def _change_cata(self):
        """
        some cataphora affects the coref chain, move the coref chain to its cataphoric entity

        Example:
            45-1	2047-2048	I	person	giv	_	_
            45-2	2049-2051	'm	_	_	_	_
            45-3	2052-2053	a	person[145]	giv[145]	cata|coref	45-1[0_145]|49-8[0_145]
            45-4	2054-2062	graduate	person[145]	giv[145]	_	_
            45-5	2063-2070	student	person[145]	giv[145]	_	_
            45-6	2071-2072	.	_	_	_	_
            45-7	2073-2074	"	_	_	_	_
        """
        for k1, v1 in self.doc.items():
            # If the cataphora does not have an antecedent
            if v1.tsv_line and 'cata' in v1.tsv_line[5]:
                for i, x in enumerate(v1.tsv_line[5].split('|')):
                    if 'cata' in x:
                        coref_rel = v1.tsv_line[6].split('|')[i]
                        cata_to = coref_rel.split('[')[0]
                        coref_id = f'0_{cata_to}'

                        coref_entity = coref_rel.split('[')[-1].split('_')[0]
                        if coref_entity != '0':
                            """
                            Example: academic_games (probably an annotation error)
                                14-19	2696-2705	attention	abstract	giv	cata	17-18[176_0]	
                            """
                            cata_to = coref_entity
                            coref_id = coref_entity

                        if coref_id not in self.doc.keys():
                            continue

                        if v1.next:
                            if v1.next != coref_id:
                                self.doc[coref_id].next = self.doc[k1].next
                                self.doc[coref_id].coref = self.doc[k1].coref
                                self.doc[coref_id].coref_type = self.doc[k1].coref_type

                            self.doc[k1].next = ''
                            self.doc[k1].coref = ''
                            self.doc[k1].coref_type = ''

            # If it's the case that the cataphora has an antecedent
            if v1.next and v1.next in self.doc.keys() and self.doc[v1.next].tsv_line and 'cata' in self.doc[v1.next].tsv_line[5]:
                v_cata = deepcopy(v1.next)
                fields = self.doc[v_cata].tsv_line
                for i, x in enumerate(fields[5].split('|')):
                    if 'cata' in x:
                        coref_rel = fields[6].split('|')[i]
                        cata_to = coref_rel.split('[')[0]
                        coref_id = f'0_{cata_to}'

                        coref_entity = coref_rel.split('[')[-1].split('_')[0]
                        if coref_entity != '0':
                            """
                            Example: academic_games (probably an annotation error)
                                14-19	2696-2705	attention	abstract	giv	cata	17-18[176_0]	
                            """
                            cata_to = coref_entity
                            coref_id = coref_entity

                        if coref_id not in self.doc.keys():
                            continue

                        if self.doc[v_cata].next == cata_to:
                            self.doc[k1].coref = ''
                            self.doc[k1].next = ''

                        # revise the antecedent
                        self.doc[k1].coref = cata_to
                        self.doc[k1].next = coref_id

                        # revise the cataphoric entity only if the current cataphoric entity has a next coref
                        if self.doc[v_cata].next and self.doc[v_cata].next != cata_to:
                            self.doc[coref_id].next = self.doc[v_cata].next
                            self.doc[coref_id].coref = self.doc[v_cata].coref
                            self.doc[coref_id].coref_type = self.doc[v_cata].coref_type

                        # revise the current entity with the cataphoric coref type
                        self.doc[v_cata].next = ''
                        self.doc[v_cata].coref = ''
                        self.doc[v_cata].coref_type = ''

    def _remove_excluded_heads(self):
        """
        If the head is not eligible, delete it

        Example:
            You 'll probably have more basil than you could possibly eat fresh , so plan on storing [some] in the fridge .
        """
        NOT_INCLUDED = ['some']
        for k_ante, v_ante in self.doc.items():
            if v_ante.next:
                k_next = deepcopy(v_ante.next)
                if k_next in self.doc.keys() and self.doc[k_next].tok in NOT_INCLUDED:
                    if self.doc[k_next].next:
                        v_ante.next = self.doc[k_next].next
                        v_ante.coref = self.doc[k_next].coref
                        v_ante.coref_type = self.doc[k_next].coref_type

                    self.doc[k_next] = Coref()
                    self.doc[k_next].delete = True

    def _remove_singleton(self):
        """
        Remove the entities that have no coref relations with other mentions
        """
        coref_next = [v.next for v in self.doc.values()]
        valid_coref = []
        for k,v in self.doc.items():
            if self.if_singletons:
                if v.cur and not v.num:
                    valid_coref.append(k)
            else:
                if k in coref_next or v.next != '':
                    valid_coref.append(k)

        return valid_coref

    def _remove_deleted_relations(self):
        """
        Some coref relations are removed by previous functions. This function is to remove those relations.
        """
        for k, _coref in self.doc.items():
            if self.doc[_coref.next] == 1:
                a = 1

    def process(self, new_id2entity):
        self._remove_junk()
        self.new_id2entity = new_id2entity
        self.last_e = sorted([int(x) for x in self.doc.keys() if not x.startswith('0_')], reverse=True)[0] + 30
        self._remove_nested_coref()
        self._expand_acl()
        self._verb_contract()
        self._appos_merge()
        self._change_cata()
        self._remove_compound()
        self._remove_bridge()
        self._remove_cop()
        self._remove_nmodposs()
        self._break_chain()
        self._remove_excluded_heads()
        self._remove_nested_coref()
        valid_coref = self._remove_singleton()

        # gum output for acl_span
        # valid_coref = list(self.doc.keys())
        return self.doc, valid_coref, self.new_id2entity
