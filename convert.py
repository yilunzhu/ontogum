import io, os
import numpy as np
import re


def find_all_child(sent: list, current_node: str):
    for fields in sent:
        current_node = fields[0]
        parent = fields[[-5]]

class ConvertGUM:
    def __init__(self, docs):
        self.docs = docs
        self.expand_acl()
        # self.remove_compound()
        # self.remove_cop()

    def check_empty(self, doc_name: str, i: int, j: int):
        """
        If all the corefs are deleted, fill in a "_"
        :return: update self.docs
        """
        if self.docs[doc_name][i][j][-1] == '':
            self.docs[doc_name][i][j][-1] = '_'

    def find_span_end(self, doc_name: str, doc: list, i: int, coref_num: str):
        for index in range(j + 1, len(doc[i])):
            coref_match = doc[i][index][-1]
            if coref_num + ')' in coref_match:
                self.docs[doc_name][i][index][-1] = coref_match.replace(coref_num + ')', '')
                self.check_empty(doc_name, i, index)
                break

    def find_span_start(self, doc_name: str, doc: list, i: int, coref_num: str):
        for index in range(j-1, 0, -1):
            coref_match = doc[i][index][-1]
            if '(' + coref_num in coref_match:
                self.docs[doc_name][i][index][-1] = coref_match.replace('(' + coref_num, '')
                self.check_empty(doc_name, i, index)
                break

    def expand_acl(self):
        """
        If the acl contains a coref, expand the span to its head if the head does not indicate a span
        :return: update self.docs
        """
        for doc_name, doc in self.docs.items():
            for i in range(len(doc)):
                for j in range(len(doc[i])):
                    func = doc[i][j][7]
                    coref = doc[i][j][-1]
                    if 'acl' in func and coref != '_':
                        # TODO: ((, 3 examples
                        if len(re.findall('\(', coref)) == 1:
                            a = 1

    def remove_compound(self):
        """
        if the func is 'compound' and (1) not NNP/NNPS, (2) has coref, (3) (0-9), (4) open bracket, (5) close bracket?,
        (6) many open brackets, remove the last one, (7) many close brackets, remove the first one
        :update self.docs
        """
        for doc_name, doc in self.docs.items():
            for i in range(len(doc)):
                for j in range(len(doc[i])):
                    # fields = line.split()
                    func = doc[i][j][7]
                    pos = doc[i][j][4]
                    coref = doc[i][j][-1]
                    if 'NNP' not in pos and coref != '_' and func == 'compound':
                        # case 1: ()
                        if re.search('\([0-9]+\)', coref) != None:
                            removed = re.search('\([0-9]+\)', coref).group()
                            # doc[i][j][-1] = coref.replace(removed, '')
                        elif re.findall('\([0-9]+', coref):
                            # case 2: ( & ((
                            # if len(re.findall('\([0-9]+', coref)) == 1:
                            #     match = re.search('\(([0-9]+)', coref)
                            #     coref_num = match.group(1)
                            #     removed = match.group(0)
                            # # case 3: ((
                            # elif len(re.findall('\([0-9]+', coref)) > 1:
                            removed = re.findall('\([0-9]+', coref)[-1]
                            coref_num = removed[1:]

                            # doc[i][j][-1] = coref.replace(removed, '')
                            self.find_span_end(doc_name, doc, i, coref_num)
                            # for index in range(j+1, len(doc[i])):
                            #     coref_match = doc[i][index][-1]
                            #     if coref_num+')' in coref_match:
                            #         self.docs[doc_name][i][index][-1] = coref_match.replace(coref_num+')', '')
                            #         if self.docs[doc_name][i][index][-1] == '':
                            #             self.docs[doc_name][i][index][-1] = '_'
                            #         break

                        elif re.findall('[0-9]+\)', coref):
                            # case 4: ) & ))
                            # if len(re.findall('[0-9]+\)', coref)) == 1:
                            #     match = re.search('([0-9]+\))', coref)
                            #     coref_num = match.group(1)
                            #     removed = match.group(0)
                            # # case 5: ))
                            # elif len(re.findall('[0-9]+\)', coref)) > 1:
                            removed = re.findall('[0-9]+\)', coref)[0]
                            coref_num = removed[:-1]
                            # for index in range(j-1, 0, -1):
                            #     coref_match = doc[i][index][-1]
                            #     if '('+coref_num in coref_match:
                            #         self.docs[doc_name][i][index][-1] = coref_match.replace('('+coref_num, '')
                            #         if self.docs[doc_name][i][index][-1] == '':
                            #             self.docs[doc_name][i][index][-1] = '_'
                            #         break
                        self.docs[doc_name][i][j][-1] = coref.replace(removed, '')
                        self.check_empty(doc_name, i, j)
                        # if docs[doc_name][i][j][-1] == '':
                        #     self.docs[doc_name][i][j][-1] = '_'

    def remove_cop(self):
        """
        :update self.docs
        """
        for doc_name, doc in self.docs.items():
            for i in range(len(doc)):
                for j in range(len(doc[i])):
                    if doc[i][j][-4] == 'cop':
                        pointing = doc[i][j][-5]
                        for m in range(j+1, len(doc[i])):
                            if doc[i][m][0] == pointing and doc[i][m][-1] != "_":
                                coref = doc[i][m][-1]
                                # case 1: ()
                                if re.search('\([0-9]+\)', coref):
                                    removed = re.search('\([0-9]+\)', coref).group()
                                # case 2: (
                                elif re.search('\([0-9]+', coref):
                                    # strip (
                                    removed = re.findall('\([0-9]+', coref)[0]
                                    coref_num = removed[1:]
                                    self.find_span_end(doc_name, doc, i, coref_num)
                                    # for index in range(m+1, len(doc[i])):
                                    #     if coref_num+')' in doc[i][index][-1]:
                                    #         self.docs[doc_name][i][index][-1] = doc[i][index][-1].replace(coref_num+')', '')
                                    #         if self.docs[doc_name][i][index][-1] == '':
                                    #             self.docs[doc_name][i][index][-1] = '_'
                                    #         break
                                elif re.search('[0-9]+\)', coref):
                                    # case 3: )
                                    removed = re.findall('[0-9]+\)', coref)[-1]
                                    coref_num = removed[:-1]
                                    self.find_span_start(doc_name, doc, i, coref_num)
                                    # for index in range(m-1, 0, -1):
                                    #     if '('+coref_num in doc[i][index][-1]:
                                    #         self.docs[doc_name][i][index][-1] = doc[i][index][-1].replace(
                                    #             '('+coref_num, '')
                                    #         if self.docs[doc_name][i][index][-1] == '':
                                    #             self.docs[doc_name][i][index][-1] = '_'
                                    #         break
                                self.docs[doc_name][i][m][-1] = doc[i][m][-1].replace(removed, '')
                                self.check_empty(doc_name, i, m)
                                # if self.docs[doc_name][i][m][-1] == '':
                                #     self.docs[doc_name][i][m][-1] = '_'


    def remove_(self):
        return ''

    def remove_order(self):
        return ''

    def remove_coord(self):
        return ''

    def remove_appos(self):
        return ''

    def remove_singleton(self):
        return ''
