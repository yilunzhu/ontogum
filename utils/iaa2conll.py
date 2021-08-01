import io, os, sys
import re
from copy import deepcopy
from argparse import ArgumentParser


def to_text(lst):
    text = ""
    for line in lst:
        new_line = line + "\n"
        text += new_line
    return text


def find_list(file):
    file_list = []
    with io.open(file) as f:
        for line in f.readlines():
            if line.startswith("GUM"):
                file_list.append(line.strip())
    return file_list


def read_tsv_file(file):
    lst = []
    with io.open(file, encoding="utf8") as f:
        for line in f.readlines():
            if "\t" in line:
                lst.append(line)
    return lst


def read_conll_file(file):
    conll_out = []
    with io.open(file, encoding="utf8") as f:
        for i, line in enumerate(f.read().split('\n')):
            if "\t" in line:
                fields = line.strip().split("\t")
                if len(fields) == 2:
                    corefs = "_"
                else:
                    corefs = fields[2]
                if corefs == '_':
                    corefs = '-'
                else:
                    while ')(' in corefs:
                        corefs = re.sub('\)\(', ')|(', corefs)
                    while re.search('[0-9]\([0-9]', corefs):
                        corefs = re.sub('([0-9])(\([0-9])', '\g<1>|\g<2>', corefs)
                    while re.search('[0-9]\)[0-9]', corefs):
                        corefs = re.sub('([0-9]\))([0-9])', '\g<1>|\g<2>', corefs)
                new_line = '\t'.join(fields[:-1] + [corefs])
                conll_out.append(new_line)
    return conll_out


def read_dep_file(file):
    dic = {}
    filename = file.split('/')[-1].split('.')[0]
    with io.open(file, encoding="utf8") as f:
        sents = f.read().split('\n\n')
        for sent in sents:
            if sent == '' or sent == '\n':
                continue
            sent_id = re.search(f'# sent_id = {filename}-([0-9]+?)\n', sent).group(1)
            speaker = re.search('# speaker=([\w\W]+?)\n', sent).group(1) if re.search('# speaker=([\w\W]+?)\n', sent) else '-'
            dic[sent_id] = speaker
    return dic


def build_conll(conll, tsv, dep, file_fields, doc_id):
    genre = file_fields.split('_')[1]
    doc = file_fields.split('_')[2]
    in_text = [f"#begin document ({genre}/{doc}); part 000"]
    for i in range(len(conll)):
        if i == 22:
            a = 1
        conll_fields = conll[i].split("\t")
        tsv_fields = tsv[i].split("\t")
        doc_key = f"{genre}/{doc}"
        sent_id = int(tsv_fields[0].split("-")[0]) - 1
        token_id = int(tsv_fields[0].split("-")[1]) - 1
        if token_id == 0 and i != 0:
            in_text.append("")
        token = conll_fields[1]
        coref = conll_fields[-1]
        fields = [doc_key, str(doc_id), str(token_id), token, "-", "-", "-", "-", "-", f"{dep[str(sent_id+1)]}", "*", "*", "*", "*", "*",
                  "*", coref]
        in_text.append("\t".join(fields))

    in_text.append("")
    in_text.append("#end document")
    return in_text


def write_file(filename, lst):
    text = to_text(lst)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)


def main(coref_path, dep_path):
    docs = {}

    for filename in os.listdir(coref_path):
        if '.tsv' not in filename:
            continue
        name_splited = filename.split('_')
        file_fields = f'GUM_{name_splited[1]}_{name_splited[2]}'
        conll_file = coref_path + os.sep + 'conll' + os.sep + filename.split('.')[0]+'.conll'

        tsv_file = coref_path + os.sep + filename.split(".")[0] + ".tsv"
        dep_file = dep_path + os.sep + file_fields + ".conllu"
        # tsv_file = coref_path + os.sep + "tsv" + os.sep + filename.split(".")[0] + ".tsv"
        out = build_conll(read_conll_file(conll_file), read_tsv_file(tsv_file), read_dep_file(dep_file), file_fields, 0)

        write_file("../iaa/onto_conll" + os.sep + f"{file_fields}.v4_gold_conll", out)

    print("Done!")


if __name__ == "__main__":
    iaa_coref_path = ".."+os.sep+"iaa"
    gum_dep_path = ".."+os.sep+"gum"+os.sep+"dep"

    main(iaa_coref_path, gum_dep_path)
