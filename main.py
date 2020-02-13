from process_data import gum_merge
from convert import ConvertGUM
import re


def case(docs):
    count = 0
    for doc_name, doc in docs.items():
        for sent in doc:
            for fields in sent:
                if fields.split()[-4] == 'cop':
                    count += 1
    print(count)


def main(gum_dir):
    docs = gum_merge(gum_dir)
    # case(docs)
    convert = ConvertGUM(docs)
    return ''

if __name__ == '__main__':
    gum_dir = 'gum'
    main(gum_dir)
