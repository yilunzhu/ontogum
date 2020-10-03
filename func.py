import io, os, sys
import re
from copy import deepcopy
from process_data import Coref
from nltk import word_tokenize


class Convert(object):
    def __init__(self, doc: dict, antecedent_dict, group_dict):
        self.antecedent_dict = antecedent_dict
        self.group_dict = group_dict
        self.doc = doc

    def _expand_acl(self):
        """
        If the acl contains a coref, expand the span to its head if the head does not indicate a span
        :return: update self.docs

        to restore the conll: '\n'.join(['\t'.join(x) for x in doc[i]])
        """
        for k, _coref in self.doc.items():
            if _coref.acl_children:
                _coref.span_len += len(_coref.acl_children)

    def _remove_compound(self):
        """
        if the func is 'compound' and (1) not NNP/NNPS, (2) has coref, remove coref relations


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
                self.doc[k] = Coref()
                # _coref.coref_type = ''
                # _coref.next = ''
                # _coref.coref = ''

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
        TODO: Bridging and coref has the same next()
        """
        for k, _coref in self.doc.items():
            if k == '0_45-1':
                a = 1
            if _coref.head_func != '' and _coref.next in self.doc.keys() and self.doc[_coref.next].child_cop == True:
                # A -> B & B -> C ====> A -> C
                # remove B
                new_coref, new_next, coref_type = self.doc[_coref.next].coref, self.doc[_coref.next].next, self.doc[_coref.next].coref_type
                self.doc[_coref.next].delete = True
                _coref.coref = new_coref
                _coref.next = new_next
                _coref.coref_type = coref_type

    def _reduceVspan(self):
        """
        If the head of span is V.*, reduce it to V
        """
        for _coref in self.doc.values():
            if _coref.head_func.startswith('V') and _coref.span_len > 1:
                _coref.func = _coref.head_func
                _coref.pos = _coref.head_pos
                _coref.span_len = 1
        return

    def _break_chain(self):
        """
        If two mentions do not obey the specificity scale, break the coref chain

        simple way to break currently:
        the > a

        Specificity scale in the OntoNotes guideline:
        Proper noun > Pronoun > Def. NP > Indef. spec. NP > Non-spec. NP
        John 		> He 	  > the man > a man I know 	  > man
        """
        for k, _coref in self.doc.items():
            if k == '0_45-1':
                a = 1
            if _coref.appos:
                continue
            # cur_toks = word_tokenize(_coref.tok)
            # cur_pos = _coref.pos
            if _coref.next and _coref.next != '0' and _coref.next in self.doc.keys() and self.doc[_coref.next].definite == False:
                # next_toks = word_tokenize(self.doc[_coref.next].tok)
                # next_pos = self.doc[_coref.next].pos
                # next_head_pos = self.doc[_coref.next].head_pos

                """
                If the chain's next is a definite entity and there are in the same sentence, do not break the chain
                - Warning: This is not a valid operation but avoids some annotation errors
                """
                next_next = deepcopy(self.doc[_coref.next].next)
                if next_next and self.doc[next_next].tok == 'she':
                    next_sent_id = self.doc[_coref.next].text_id.split('-')[0]
                    next_next_sent_id = self.doc[next_next].text_id.split('-')[0]
                    if next_sent_id == next_next_sent_id:
                        print(f'Warning: Skip breaking chains in Line {next_sent_id}. It should not happen too often.')
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

            # # generic nouns
            # elif next_pos and not re.search('PR|DT', next_pos) and 'NNP' not in next_head_pos:
            #     a = 1

    def _remove_coord(self):
        """
        deal with coordinations
        """
        return

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
        last_e = sorted([int(x) for x in self.doc.keys() if not x.startswith('0_')], reverse=True)[0] + 30
        loop_doc = deepcopy(self.doc)
        for k1, v in loop_doc.items():
            k1_sent_id = v.text_id.split('-')[0]
            for k2, next_v in loop_doc.items():
                if k1 == '100' and k2 == '233':
                    a = 1
                k2_sent_id = next_v.text_id.split('-')[0]
                if k1_sent_id == k2_sent_id and v.coref == next_v.text_id and (v.coref_type == 'appos' or next_v.dep_appos):

                    # create a new e as the new big span for the apposition
                    new_k1 = str(last_e+1)
                    self.doc[new_k1] = deepcopy(self.doc[k1])
                    self.doc[new_k1].cur = new_k1
                    self.doc[new_k1].coref = next_v.coref
                    self.doc[new_k1].next = next_v.next
                    self.doc[new_k1].coref_type = next_v.coref_type
                    self.doc[new_k1].func += ' ' + next_v.func
                    self.doc[new_k1].pos += ' ' + next_v.pos
                    self.doc[new_k1].span_len += next_v.span_len
                    self.doc[new_k1].tok += ' ' + next_v.tok
                    self.doc[new_k1].e_type = v.e_type
                    self.doc[new_k1].new_e = True

                    last_e += 1

                    self.doc[k1].dep_appos = True
                    self.doc[k1].appos_point_to = new_k1

                    self.doc[k2].appos_father = k1
                    self.doc[k2].coref = ''
                    self.doc[k2].next = ''
                    self.doc[k2].coref_type = ''

        # if the next entity is an appos, redirect the coref chain
        for k1, v in self.doc.items():
            for k2, next_v in self.doc.items():
                if v.next == k2 and next_v.appos_point_to:
                    self.doc[k1].next = next_v.appos_point_to

    def _remove_nmodposs(self):
        """
        Example: [Zurbarán ’s] cycle of Jacob and his Sons
        """
        for k,v in self.doc.items():
            if k == '184':
                a = 1
            if k in self.doc.keys() and v.next in self.doc.keys() and v.next != '' and self.doc[v.next].nmod_poss:
                next = v.next
                self.doc[k].coref = self.doc[v.next].coref
                self.doc[k].coref_type = self.doc[v.next].coref_type
                self.doc[k].next = self.doc[v.next].next

                self.doc[next].coref = ''
                self.doc[next].next = ''
                self.doc[next].coref_type = ''

    def _remove_iwithini(self):
        """
        Example: [a man ... his]_1 ... []_1
        """
        return

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
            if k1 == '145':
                a = 1

            # If the cataphora does not have an antecedent
            if 'cata' in v1.tsv_line[5]:
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
            if v1.next and v1.next in self.doc.keys() and 'cata' in self.doc[v1.next].tsv_line[5]:
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

                    self.doc[k_next].next = ''
                    self.doc[k_next].coref = ''
                    self.doc[k_next].coref_type = ''

    def _remove_singleton(self):
        """
        Remove the entities that have no coref relations with other mentions
        """
        coref_next = [v.next for v in self.doc.values()]
        valid_coref = []
        for k,v in self.doc.items():

            # test
            if k == '0_45-1':
                a = 1
            # if v.appos_father and v.appos_father not in coref_next:
            #     continue
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

    def process(self):
        self._expand_acl()
        self._appos_merge()
        self._change_cata()
        self._remove_compound()
        self._remove_bridge()
        self._remove_cop()
        self._break_chain()
        self._reduceVspan()
        # self._remove_coord()
        # self._remove_iwithini()
        self._remove_nmodposs()
        self._remove_excluded_heads()
        valid_coref = self._remove_singleton()

        # gum output for acl_span
        # valid_coref = list(self.doc.keys())
        return self.doc, valid_coref
