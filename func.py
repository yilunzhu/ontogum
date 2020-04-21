import io, os, sys
from process_data import Coref

class Convert(object):
    def __init__(self, doc: dict):
        self.doc = doc
        self.expand_acl()
        self.remove_compound()
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
        for _coref in self.doc.values():
            # currently remove the question example. To avoid deleting such examples, add another condition
            # "_coref.pos not startswith('det')"
            if 'compound' in _coref.func and ('NNP' not in _coref.pos and 'NNPS' not in _coref.pos):
                _coref.coref_type = ''
                _coref.next = ''
                _coref.coref = ''
        return

    def remove_cop(self):
        """
        if (1) two coref mentions are in the same sentence, (2) a copula dep func is the child of the first one,
        remove the coref relations between the two and move the second coref to the first one
        """
        for k, _coref in self.doc.items():
            if _coref.head_func != '' and _coref.text_id.split('-')[0] == _coref.coref.split('-')[0] \
                    and _coref.next in self.doc.keys() and self.doc[_coref.next].child_cop == True \
                    and _coref.head_func == 'nsubj':
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

        Specificity scale:
        Proper noun > Pronoun > Def. NP > Indef. spec. NP > Non-spec. NP
        John 		> He 	  > the man > a man I know 	  > man
        """
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
        return

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
        return
