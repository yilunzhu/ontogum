import io, os, sys
import re
from copy import deepcopy


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
    prev_mentions = []
    mul_mentions = []
    with io.open(file, encoding="utf8") as f:
        for line in f.readlines():
            if "\t" in line:
                fields = line.strip().split("\t")
                if len(fields) == 2:
                    corefs = "_"
                else:
                    corefs = fields[2]
                corefs = re.split(r"\(|\)", corefs)
                #                 print(corefs)
                corefs = [x for x in corefs if re.search("[0-9]", x)]
                if corefs:
                    for i in corefs:
                        if i in prev_mentions:
                            mul_mentions.append(i)
                        prev_mentions.append(i)

    mul_mentions = set(mul_mentions)
    lst = []
    with io.open(file, encoding="utf8") as f:
        for line in f.readlines():
            if "\t" in line:
                fields = line.strip().split("\t")
                if len(fields) == 2:
                    corefs = "_"
                else:
                    corefs = fields[2]
                #                 corefs = fields[2]
                numbers = re.findall("[0-9]+", corefs)
                for num in numbers:
                    if num not in mul_mentions:
                        left = ""
                        right = ""
                        rm = deepcopy(num)
                        if corefs.index(num) != 0:
                            left = corefs[corefs.index(num) - 1]
                        if corefs.index(num) + len(num) != len(corefs):
                            right = corefs[corefs.index(num) + len(num)]
                        if left and left in ["(", "|"]:
                            rm = left + rm
                        if right and right == ")":
                            rm = rm + right
                        corefs = corefs.replace(rm, "")
                if corefs == "":
                    corefs = "-"
                elif corefs == "_":
                    corefs = "-"
                elif corefs[0] == "|":
                    corefs = corefs[1:]
                elif corefs[-1] == "|":
                    corefs = corefs[:-1]
                elif ")(" in corefs:
                    corefs = corefs.replace(")(", ")|(")
                else:
                    if re.search("[0-9][\(\)][0-9]", corefs):
                        corefs = re.sub("([0-9])(\()", "\g<1>|\g<2>", corefs)
                        corefs = re.sub("(\))([0-9])", "\g<1>|\g<2>", corefs)
                new_fields = fields[:-1] + [corefs]
                fields = "\t".join(new_fields)

                lst.append(fields)

    return lst


def build_conll(conll, tsv, file_fields, doc_id):
    genre = file_fields[1]
    doc = file_fields[2]
    in_text = [f"#begin document ({genre}/{doc}); part 000"]
    for i in range(len(conll)):
        conll_fields = conll[i].split("\t")
        tsv_fields = tsv[i].split("\t")
        doc_key = f"{genre}/{doc}"
        # sent_id = int(tsv_fields[0].split("-")[0]) - 1
        token_id = int(tsv_fields[0].split("-")[1]) - 1
        if token_id == 0 and i != 0:
            in_text.append("")
        token = conll_fields[1]
        coref = conll_fields[-1]
        fields = [doc_key, str(doc_id), str(token_id), token, "_", "_", "_", "_", "_", "_", "*", "*", "*", "*", "*",
                  "*", coref]
        in_text.append("\t".join(fields))

    in_text.append("")
    in_text.append("#end document")
    return in_text


def write_file(filename, lst):
    text = to_text(lst)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)


def main(coref_path, gum_file_lists=None, use_gumby=False):
    if use_gumby:
        gumby_gold = []
    else:
        train_list = []
        dev_list = []
        test_list = []
        train = []
        dev = []
        test = []

        for filename in os.listdir(gum_file_lists):
            file_path = gum_file_lists + os.sep + filename
            if "train" in filename:
                train_list = find_list(file_path)
            elif "dev" in filename:
                dev_list = find_list(file_path)
            else:
                test_list = find_list(file_path)

    genres = ["academic", "bio", "fiction", "interview", "news", "voyage", "whow", "reddit"]

    for genre in genres:
        for filename in os.listdir(coref_path + os.sep + "conll"):
            if genre in filename:
                file_fields = filename.split(".")[0].split("_")
                conll_file = coref_path + os.sep + "conll" + os.sep + filename
                tsv_file = coref_path + os.sep + "tsv" + os.sep + filename.split(".")[0] + ".tsv"

                if use_gumby:
                    gumby_gold += build_conll(read_conll_file(conll_file), read_tsv_file(tsv_file), file_fields, 0)
                else:
                    if filename.split(".")[0] in train_list:
                        train += build_conll(read_conll_file(conll_file), read_tsv_file(tsv_file), file_fields, 0)
                    elif filename.split(".")[0] in dev_list:
                        dev += build_conll(read_conll_file(conll_file), read_tsv_file(tsv_file), file_fields, 0)
                    elif filename.split(".")[0] in test_list:
                        test += build_conll(read_conll_file(conll_file), read_tsv_file(tsv_file), file_fields, 0)
                    else:
                        sys.stderr.write(f"ERROR: file {filename} not in list.\n")
                        # sys.exit()

        # assert len(conll_lst) == len(tsv_lst)
    if use_gumby:
        write_file("out" + os.sep + "test.gumby.english.v4_gold_conll", gumby_gold)
    else:
        write_file("out" + os.sep + "train.gum.english.v4_gold_conll", train)
        write_file("out" + os.sep + "dev.gum.english.v4_gold_conll", dev)
        write_file("out" + os.sep + "test.gum.english.v4_gold_conll", test)

    sys.stderr.write("Done!")


if __name__ == "__main__":
    mode = sys.argv[1]

    if mode == "gum":
        # GUM
        gum_train_coref_path = "gum" + os.sep + "coref"
        gum_file_lists = "file_lists"
        main(gum_train_coref_path, gum_file_lists=gum_file_lists, use_gumby=False)
    elif mode == "gumby":
        # GUMBY gold
        gumby_coref_path = "gumby_gold"
        main(gumby_coref_path, use_gumby=True)
    else:
        """
        You can add your mode here.
        """
        sys.stderr.write("unrecognized mode. Please enter either gum or gumby.")
        sys.exit()
