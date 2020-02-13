import io, os


def gum_merge(data_dir):
    dep_dir = data_dir + os.sep + 'dep' + os.sep + 'ud'
    conll_dir = data_dir + os.sep + 'coref' + os.sep + 'conll'

    docs = {}
    for dep_filename in os.listdir(dep_dir):
        doc = []
        sent_lst =[]
        filename = dep_filename.split('.')[0]

        conll_f = open(conll_dir + os.sep + filename + '.conll', encoding='utf-8').readlines()
        dep_f = open(dep_dir + os.sep + dep_filename, encoding='utf-8').readlines()
        count = 0
        for i in range(len(dep_f)):
            if dep_f[i].startswith('\n'):
                if len(sent_lst) > 0:
                    doc.append(sent_lst)
                sent_lst = []
            elif not dep_f[i].startswith('#'):
                dep_fields = dep_f[i].split()
                dep_word = dep_fields[1]
                for j in range(count, len(conll_f)):
                    if not (conll_f[j].startswith('#') or conll_f[j].startswith('\n')):
                        conll_word = conll_f[j].split()[1]
                        if dep_word != conll_word:
                            j += 1
                        else:
                            coref = conll_f[j].split()[2]
                            # sent_lst.append(dep_f[i].strip('\n') + "\t" + coref)
                            sent_lst.append(dep_f[i].split()+[coref])
                            # count = j
                            break
        docs[filename] = doc
    return docs

# gum_dir = 'gum'
# gum_merge(data_dir=gum_dir)
