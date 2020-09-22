import io, os


def write_file(out_dir, output_string):
    with io.open(out_dir, 'w', encoding='utf-8') as f:
        f.write(output_string)


def remove_singleton(e, non_singleton, coref_fields, line_id):
    if e:
        coref_fields[3] = '|'.join([x for x in coref_fields[3].split('|') if e not in x])
        coref_fields[4] = '|'.join([x for x in coref_fields[4].split('|') if e not in x])
    else:
        if f'0_{line_id}' not in non_singleton:
            coref_fields[3], coref_fields[4] = '', ''
    return coref_fields[3], coref_fields[4]


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


def to_tsv(doc, coref_article, out_dir, non_singleton, new_id2entity):
    converted_article = ''
    added_coref = []
    last_coref = ''

    new_entities = {k:v for k,v in doc.items() if v.new_e}
    for k, v in new_entities.items():
        tok_id = int(v.text_id.split('-')[-1])
        ids = {f'{v.text_id.split("-")[0]}-{tok_id+i}': k for i in range(v.span_len)}
        for id, e in ids.items():
            if id not in new_id2entity.keys():
                new_id2entity[id] = []
            new_id2entity[id].append(e)
            a = 1

    for line in coref_article:
        if line.startswith('#') or line == '':
            converted_article += line + '\n'
            continue

        coref_fields = line.strip().split('\t')
        line_id, token = coref_fields[0], coref_fields[2]
        coref_fields[-2], coref_fields[-1] = '', ''

        # test
        if line_id == '61-36':
            a = 1

        # entity info
        entities = ['' if '[' not in x else x.strip(']').split('[')[1] for x in coref_fields[3].split('|')]
        # deal with new entities, such as appositions
        if line_id in new_id2entity.keys():
            new_id = new_id2entity[line_id]
            entities += new_id

        # loop every possible entities in a single line
        for e in entities:
            if e in doc.keys():
                id = e
            elif f'0_{line_id}' in doc.keys():
                id = f'0_{line_id}'
            else:
                id = ''

            # remove deleted entities in func.py
            if id in doc.keys() and doc[id].delete == True:
                if e:
                    coref_fields[3] = '|'.join([x for x in coref_fields[3].split('|') if e not in x])
                    coref_fields[4] = '|'.join([x for x in coref_fields[3].split('|') if e not in x])
                else:
                    if '|' in coref_fields[3]:
                        raise ValueError('The line with fake id has deleted entities. Revise the code.')
                    coref_fields[3] = ''
                    coref_fields[4] = ''
                continue

            # remove singleton
            if id not in non_singleton:
                coref_fields[3], coref_fields[4] = remove_singleton(e, non_singleton, coref_fields, line_id)
                continue

            if e in doc.keys():
                cur, next = doc[id].cur, doc[id].next
                if doc[id].acl_children:
                    last_coref = id

                # check appositions, handle coref_fields[3, 4]
                if e not in coref_fields[3] and e not in coref_fields[4]:
                    if doc[e].span_len == 1:
                        coref_fields[3] += f'|{doc[e].e_type}'
                        coref_fields[4] += f'|{doc[e].seen}'
                    else:
                        coref_fields[3] += f'|{doc[e].e_type}[{e}]'
                        coref_fields[4] += f'|{doc[e].seen}[{e}]'

                if next == '':
                    # if next originally exists but deleted by func.py, remove it in coref_fields
                    if doc[e].nmod_poss:
                        coref_fields[3] = '|'.join([x for x in coref_fields[3].split('|') if cur not in x])
                        coref_fields[4] = '|'.join([x for x in coref_fields[4].split('|') if cur not in x])
                    continue

                if next.startswith('0_'):
                    next = '0'

                coref = f'{doc[id].coref}[{next}_{cur}]'

                # check if it's the beginning of a mention, if not, continue
                if coref in added_coref:
                    continue

                coref_fields[-2] += f'|{doc[id].coref_type}'
                coref_fields[-1] += f'|{coref}'
                added_coref.append(coref)

            # if the current token is not an entity, but has coref
            elif f'0_{line_id}' in doc.keys():

                # if next coref is removed
                if doc[id].next == '' and doc[id].coref_type == '':
                    if '0_' not in doc[id].cur and doc[id].cur not in coref_fields[3] and coref_fields[3] != '_':
                        coref_fields[-3] += f'[{doc[id].cur}]'
                        coref_fields[3] += f'[{doc[id].cur}]'
                    pass

                # if the current word is not an named entity and the coref next is neither an named entity
                # but has coref relations
                elif doc[id].cur.startswith('0_') and doc[id].next.startswith('0_'):
                    coref_fields[-2] += doc[id].coref_type
                    coref_fields[-1] += doc[id].coref

                # if the current word is not an named entity while the next coref is an named entity
                # and has coref relation
                elif doc[id].cur.startswith('0_'):
                    coref_fields[-2] += doc[id].coref_type
                    coref_fields[-1] += f'{doc[id].coref}[{doc[id].next}_0]'

                # if changed in func, such in function "remove_appos"
                else:
                    coref_fields[-3] += f'[{doc[id].cur}]'
                    coref_fields[3] += f'[{doc[id].cur}]'

        # add expanded acl to the lines that are originally not included in the mention
        cur_sent_id, cur_tok_id = line_id.split('-')[0], line_id.split('-')[1]
        if last_coref in doc.keys() and cur_sent_id == doc[last_coref].text_id.split('-')[0] and cur_tok_id in \
                doc[last_coref].acl_children:
            coref_fields[3] += '|' + doc[last_coref].e_type + f'[{doc[last_coref].cur}]'
            coref_fields[4] += '|' + doc[last_coref].seen + f'[{doc[last_coref].cur}]'

        # if the line does not contain coref info, do not change it
        if f'0_{line_id}' not in doc.keys() and coref_fields[3] == '_':
            converted_article += line.strip() + '\n'
            continue

        # format revise
        if coref_fields[-1] == '' and coref_fields[-2] == '':
            coref_fields[-2], coref_fields[-1] = '_', '_'
        if coref_fields[3] == '' and coref_fields[4] == '':
            coref_fields[3], coref_fields[4] = '_', '_'

        coref_fields = [x.strip('|') for x in coref_fields]

        converted_article += '\t'.join(coref_fields) + '\n'

    write_file(out_dir, converted_article)
