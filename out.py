import io, os


def write_file(out_dir, output_string):
    with io.open(out_dir, 'w', encoding='utf-8') as f:
        f.write(output_string)


def get_glyph(entity_type):
    """
    This function borrows from xrenner.

    Generates appropriate Font Awesome icon strings based on entity type strings, such as
    a person icon (fa-male) for the 'person' entity, etc.

    :param entity_type: String specifying the entity type to be visualized
    :return: HTML string with the corresponding Font Awesome icon
    """
    if entity_type == "person":
        return '<i title="' + entity_type + '" class="fa fa-male"></i>'
    elif entity_type == "place":
        return '<i title="' + entity_type + '" class="fa fa-map-marker"></i>'
    elif entity_type == "time":
        return '<i title="' + entity_type + '" class="fa fa-clock-o"></i>'
    elif entity_type == "abstract":
        return '<i title="' + entity_type + '" class="fa fa-cloud"></i>'
    elif entity_type == "quantity":
        return '<i title="' + entity_type + '" class="fa fa-sort-numeric-asc"></i>'
    elif entity_type == "organization":
        return '<i title="' + entity_type + '" class="fa fa-bank"></i>'
    elif entity_type == "object":
        return '<i title="' + entity_type + '" class="fa fa-cube"></i>'
    elif entity_type == "event":
        return '<i title="' + entity_type + '" class="fa fa-bell-o"></i>'
    elif entity_type == "animal":
        return '<i title="' + entity_type + '" class="fa fa-paw"></i>'
    elif entity_type == "plant":
        return '<i title="' + entity_type + '" class="fa fa-pagelines"></i>'
    elif entity_type == "substance":
        return '<i title="' + entity_type + '" class="fa fa-flask"></i>'
    else:
        return '<i title="' + entity_type + '" class="fa fa-question"></i>'


def to_html(doc, tokens, group_dict, antecedent_dict, out_dir):
    output_string = '''<html>
<head>
	<link rel="stylesheet" href="http://corpling.uis.georgetown.edu/xrenner/css/renner.css" type="text/css" charset="utf-8"/>
	<link rel="stylesheet" href="https://corpling.uis.georgetown.edu/xrenner/css/font-awesome-4.2.0/css/font-awesome.min.css"/>
	<meta http-equiv="content-type" content="text/html; charset=utf-8"/>
</head>
<body>
<script src="http://corpling.uis.georgetown.edu/xrenner/script/jquery-1.11.3.min.js"></script>
<script src="http://corpling.uis.georgetown.edu/xrenner/script/chroma.min.js"></script>
<script src="http://corpling.uis.georgetown.edu/xrenner/script/xrenner.js"></script>\n'''

    # coref_id = 1
    skip = 0
    prev_line_id = ''
    for idx, (tok, line_id, entities, coref) in enumerate(tokens):

        if line_id == '16-18':
            a = 1

        if skip > 0:
            skip -= 1
            continue

        fake_e = f'0_{line_id}'
        length = []

        # plain words, e.g. "and"
        if entities == []:
            output_string += f'{tok}\n'
            added = True
            continue

        # words that are part of named entities, check whether coref exists
        if_coref = False
        for e in entities:

            if e in doc.keys() or fake_e in doc.keys():
                e = e if e else fake_e

                # deal with converted coref
                if doc[e].tok == '':
                    output_string += f'{tok}\n'
                    continue

                group = group_dict[e]
                coref_doc = doc[e]
                coref_id = e
                text = coref_doc.tok
                length.append(coref_doc.span_len)

                # TODO: add span information, such as "class", "definiteness", "lemma"
                title = f'&#10;core_text: {text}  &#10;coref_type: {coref_doc.coref_type}'

                coref_id = coref_id.replace('_', '').replace('-', '')
                info_string = f'''<div id="referent_{coref_id}" onmouseover="highlight_group ('{group}')" onmouseout="unhighlight_group('{group}')" class="referent" group="{group}" title="{title}"'''

                # if there is coref relation
                if e in antecedent_dict.keys():
                    info_string += f' antecedent="{antecedent_dict[e]}"'

                info_string += '><span class="entity_type">' + get_glyph(coref_doc.e_type) + '</span>\n'

                output_string += info_string
            else:
                output_string += f'{tok}\n'
                entities.remove(e)


        # when encounters multiple entities
        if length:
            length = sorted(length)
            skip = length[-1] - 1
            prev_l = 0
            for cur_l in length:
                if prev_l == cur_l:
                    continue
                s = ''
                for i in range(idx, idx+cur_l-prev_l):
                    s += f'{tokens[i][0]}\n'
                    # skip -= 1
                output_string += s + '</div>\n'
                prev_l = cur_l
                idx += prev_l

    output_string += '<script>colorize();</script>\n'
    output_string += '''</body>
    </html>'''

    write_file(out_dir, output_string)


def to_tsv(doc, coref_article, out_dir):
    converted_article = ''
    added_coref = []

    for line in coref_article:
        if line.startswith('#') or line == '':
            converted_article += line + '\n'
            continue

        coref_fields = line.strip().split('\t')
        line_id, token = coref_fields[0], coref_fields[2]
        coref_fields[-2], coref_fields[-1] = '', ''

        # test
        if line_id == '9-2':
            a = 1

        if f'0_{line_id}' not in doc.keys() and coref_fields[3] == '_':
            converted_article += line + '\n'
            continue

        # entity info
        entities = ['' if '[' not in x else x.strip(']').split('[')[1] for x in coref_fields[3].split('|')]

        for e in entities:
            if e in doc.keys():
                cur, next = doc[e].cur, doc[e].next

                if next == '':
                    continue

                if cur.startswith('0_'):
                    cur = '0'
                if next.startswith('0_'):
                    next = '0'

                coref = f'{doc[e].coref}[{next}_{cur}]'
                if coref in added_coref:
                    continue

                if coref_fields[-2] and coref_fields[-1]:
                    coref_fields[-2] += '|'
                    coref_fields[-1] += '|'
                coref_fields[-2] += doc[e].coref_type
                coref_fields[-1] += coref
                added_coref.append(coref)

        if coref_fields[-1] == '' and coref_fields[-2] == '':
            coref_fields[-2], coref_fields[-1] = '_', '_'

        converted_article += '\t'.join(coref_fields) + '\n'

    write_file(out_dir, converted_article)
