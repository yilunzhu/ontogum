import io, os, sys
from process_data import Coref
from nltk import word_tokenize

class Convert(object):
    def __init__(self, doc: dict, antecedent_dict, group_dict):
        self.antecedent_dict = antecedent_dict
        self.group_dict = group_dict
        self.doc = doc
        self.expand_acl()
        self.remove_compound()
        self.remove_bridge()
        self.remove_cop()
        self.reduceVspan()
        self.break_chain()
        self.order()
        self.remove_coord()
        self.remove_appos()
        self.remove_iwithini()
        self.remove_singleton()

    def expand_acl(self):
        """
        If the acl contains a coref, expand the span to its head if the head does not indicate a span
        :return: update self.docs

        to restore the conll: '\n'.join(['\t'.join(x) for x in doc[i]])

        TODO: also advcl
        """
        return

    def remove_compound(self):
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
            if 'compound' in _coref.func and ('NNP' not in _coref.pos and 'NNPS' not in _coref.pos):
                self.doc[k] = Coref()
                # _coref.coref_type = ''
                # _coref.next = ''
                # _coref.coref = ''
        return


    def remove_bridge(self):
        """
        if the coref type contains "bridge" but not "bridge:aggr", remove that coref relation
        :return:
        """
        for k, _coref in self.doc.items():
            if 'bridge' in _coref.coref_type and _coref.coref_type != 'bridge:aggr':
                a = 1
                self.doc[k] = Coref()
                # self.doc[k].coref = ''
                # self.doc[k].next = ''
                # self.doc[k].coref_type = ''
        return

    def remove_cop(self):
        """
        if (1) two coref mentions are in the same sentence, (2) a copula dep func is the child of the first one,
        remove the coref relations between the two and move the second coref to the first one
        TODO: Bridging and coref has the same next()
        """
        for k, _coref in self.doc.items():
            if _coref.head_func != '' and _coref.next in self.doc.keys() and self.doc[_coref.next].child_cop == True:
                # A -> B & B -> C ====> A -> C
                # remove B
                new_coref, new_next = self.doc[_coref.next].coref, self.doc[_coref.next].next
                self.doc[_coref.next] = Coref()
                _coref.coref = new_coref
                _coref.next = new_next
        return

    def reduceVspan(self):
        """
        If the head of span is V.*, reduce it to V
        """
        for _coref in self.doc.values():
            if _coref.head_func.startswith('V') and _coref.span_len > 1:
                _coref.func = _coref.head_func
                _coref.pos = _coref.head_pos
                _coref.span_len = 1
        return

    def break_chain(self):
        """
        If two mentions do not obey the specificity scale, break the coref chain

        simple way to break currently:
        the > a

        Specificity scale in the OntoNotes guideline:
        Proper noun > Pronoun > Def. NP > Indef. spec. NP > Non-spec. NP
        John 		> He 	  > the man > a man I know 	  > man
        """
        for k, _coref in self.doc.items():
            cur_toks = word_tokenize(_coref.tok)
            if _coref.next and _coref.next != '0' and _coref.next in self.doc.keys():
                next_toks = word_tokenize(self.doc[_coref.next].tok)
                if 'a' in next_toks or 'an' in next_toks:
                    # break_group = self.group_dict[self.doc[_coref.next].cur]
                    break_group = max(self.group_dict.values()) + 1
                    next_coref = self.doc[_coref.next]
                    while next_coref.cur in self.antecedent_dict.keys():
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
                    del self.antecedent_dict[k]
        return

    def order(self):
        """
        order each cluster if
        (1) span is indef: NN/NNS + no def dep (a/the/determiner/poss/genitive 's)
        (2) span has antecedent
        """
        return

    def remove_coord(self):
        """
        deal with coordinations
        """
        return

    def remove_appos(self):
        """
        If coref_type==appos, remove the current coref

        Example:
            27-40	3795-3798	the	object[220]	new[220]	appos	27-42[0_220]
            27-41	3799-3803	13th	object[220]	new[220]	_	_
            27-42	3804-3812	Benjamin	object	giv	coref	27-45[221_0]
        remove 27-40 -> 27-42
        """
        for k, v in self.doc.items():
            if v.coref_type == 'appos':
                self.doc[k] = Coref()

    def remove_iwithini(self):
        """
        Examples: [a man ... his]_1 ... []_1
        """
        return

    def remove_cata(self):
        """
        remove cataphora
        """
        return

    def remove_singleton(self):
        """
        Remove the entities that have no coref relations with other mentions
        """
        coref_next = [v.next for v in self.doc.values()]
        for k,v in self.doc.items():
            if k not in coref_next and v.next == '':
                if k == '38':
                    a = 1
                a = 1
                # self.doc[k] = Coref()
