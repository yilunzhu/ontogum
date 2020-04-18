import io, os, sys

class Convert(object):
    def __init__(self, doc: dict):
        self.doc = doc
        self.expand_acl()
        self.remove_compound()
        self.remove_cop()
        self.break_chain()
        self.remove_order()
        self.remove_coord()
        self.remove_appos()
        self.remove_iwithini()
        self.remove_singleton()

    def expand_acl(self):
        return

    def remove_compound(self):
        return

    def remove_cop(self):
        return

    def break_chain(self):
        return

    def remove_order(self):
        return

    def remove_coord(self):
        return

    def remove_appos(self):
        return

    def remove_iwithini(self):
        """
        [a man ... his]_1 ... []_1
        :return:
        """
        return

    """
    also cataphora
    """

    def remove_singleton(self):
        return
