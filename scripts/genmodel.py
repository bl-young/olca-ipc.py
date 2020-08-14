"""
This is a script for generating the initial model types from the
olca-schema yaml files. To run this script you need to have PyYAML
installed, e.g.:

    pip install pyyaml

You also have to configure the YAML_DIR in this script to point to
the directory where the YAML files are located: 
    # clone the olca-schema repository to some folder
    cd <folder>
    git clone https://github.com/GreenDelta/olca-schema.git
    # <folder>/olca-schema/yaml is the path for the YAML_DIR

After this you can run this script. It will print the generated classes and
enumerations to the console:

    python genmodel.py > [.. path to generated file].py

"""

from os import path

import model

YAML_DIR = path.abspath(path.dirname(__file__)) + '/../../olca-schema/yaml'


def to_snake_case(identifier: str) -> str:
    s = ''
    for char in identifier:
        if char.isupper():
            s += '_'
            s += char.lower()
        else:
            s += char
    # if s is a Python key-word, append a `_`
    if s in ['from', 'in']:
        s += '_'
    return s


def py_type(model_type: str) -> str:
    if model_type == 'string':
        return 'str'
    if model_type == 'double':
        return 'float'
    if model_type == 'boolean':
        return 'bool'
    if model_type == 'integer':
        return 'int'
    if model_type == 'dateTime':
        return 'str'
    if model_type == 'date':
        return 'str'
    if model_type.startswith('Ref['):
        return 'Ref'
    if model_type.startswith('List['):
        list_type = py_type(list_elem_type(model_type))
        return 'List[%s]' % list_type
    return model_type


def print_class(c: model.ClassType, m: model.Model):
    parent = c.super_class if c.super_class is not None else 'object'
    t = '\nclass %s(%s):\n\n' % (c.name, py_type(parent))
    if c.doc is not None:
        t += print_docs(c)
    t += '    def __init__(self):\n'
    if c.name == 'Entity':
        t += '        self.id: str = \'\'\n'
        t += '        self.olca_type: str = \'\'\n'
    else:
        t += '        super(%s, self).__init__()\n' % c.name
    for prop in c.properties:
        attr = to_snake_case(prop.name)
        ptype = py_type(prop.field_type)
        t += '        self.%s: Optional[%s] = None\n' % (attr, ptype)
    print(t)
    print_to_json(c, m)
    print_from_json(c, m)


def print_to_json(c: model.ClassType, m: model.Model):
    t = '    def to_json(self) -> dict:\n'
    off = '        '
    if c.name == 'Entity':
        t += off + "o_type = self.olca_type\n"
        t += off + "if o_type is None:\n"
        t += off + "    o_type = type(self).__name__\n"
        t += off + "json = {'@type': o_type}\n"
        t += off + 'if self.id is not None:\n'
        t += off + "    json['@id'] = self.id\n"
        t += off + 'return json\n'
    else:
        t += off + 'json: dict = super(%s, self).to_json()\n' % c.name
        for prop in c.properties:
            attr = to_snake_case(prop.name)
            t += off + 'if self.%s is not None:\n' % attr
            is_primitive = prop.field_type[0].islower()
            is_enum = m.find_enum(prop.field_type) is not None
            is_list = prop.field_type.startswith('List[')
            if is_primitive:
                t += off + "    json['%s'] = self.%s\n" % (prop.name, attr)
            elif is_enum:
                t += off + \
                     "    json['%s'] = self.%s.value\n" % (prop.name, attr)
            elif is_list:
                t += off + "    json['%s'] = []\n" % prop.name
                t += off + "    for e in self.%s:\n" % attr
                list_type = py_type(list_elem_type(prop.field_type))
                if list_type[0].islower():
                    t += off + off + "json['%s'].append(e)\n" % prop.name
                else:
                    t += off + off + \
                         "json['%s'].append(e.to_json())\n" % prop.name
            else:
                t += off + \
                     "    json['%s'] = self.%s.to_json()\n" % (prop.name, attr)
        t += off + 'return json\n'
    print(t)


def print_from_json(c: model.ClassType, m: model.Model):
    t = '    def from_json(self, json: dict):\n'
    off = '        '
    if len(c.properties) == 0:
        t += off + "self.id = json.get('@id')\n"
    else:
        t += off + 'super(%s, self).from_json(json)\n' % c.name
        for prop in c.properties:
            attr = to_snake_case(prop.name)
            is_primitive = prop.field_type[0].islower()
            is_enum = m.find_enum(prop.field_type) is not None
            is_list = prop.field_type.startswith('List[')
            t += off + "val = json.get('%s')\n" % prop.name
            t += off + "if val is not None:\n"
            if is_primitive:
                t += off + "    self.%s = val\n" % attr
            elif is_enum:
                t += off + \
                     "    self.%s = %s(val)\n" % (attr, prop.field_type)
            elif is_list:
                t += off + "    self.%s = []\n" % attr
                t += off + "    for d in val:\n"
                list_type = list_elem_type(prop.field_type)
                if list_type[0].islower():
                    t += off + off + 'e = d\n'
                else:
                    t += off + off + 'e = %s()\n' % list_type
                    t += off + off + 'e.from_json(d)\n'
                t += off + off + 'self.%s.append(e)\n' % attr
            else:
                t += off + "    self.%s = %s()\n" % (attr, py_type(prop.field_type))
                t += off + "    self.%s.from_json(val)\n" % attr
    print(t)


def list_elem_type(list_type: str) -> str:
    t = list_type[5:(len(list_type) - 1)]
    if t.startswith('Ref['):
        return 'Ref'
    return t


def print_enum(e: model.EnumType):
    t = 'class %s(Enum):\n' % e.name
    if e.doc is not None:
        t += print_docs(e)
    for item in e.items:
        t += "    %s = '%s'\n" % (item.name, item.name)
    t += '\n'
    print(t)


def print_docs(c) -> str:
    off = '    '
    d = off + '"""'
    multi_lines = False
    docs = c.doc
    if len(docs) == 0:
        return ''
    if contains_link(docs):
        docs = remove_link(docs)
    if len(docs) < 79:
        d += docs
    else:
        multi_lines = True
        d += '\n' + off
        d += format_docs(docs.split(), len(off))
    if type(c) == model.ClassType:
        if len(c.properties) > 0 and has_prop_docs(c):
            multi_lines = True
            d += print_class_property_docs(c)
    if multi_lines:
        d += '\n' + off + '"""\n\n'
    else:
        d += '"""\n\n'
    return d


def print_class_property_docs(c: model.ClassType) -> str:
    off = '    '
    s = '\n\n'
    s += off + 'Attributes\n'
    s += off + '----------\n'
    for prop in c.properties:
        attr = to_snake_case(prop.name)
        ptype = py_type(prop.field_type)
        s += '%s%s: %s\n' % (off, attr, ptype)
        s += format_doc(prop.doc, indent=8) + '\n\n'
    return s


def format_docs(docs: list, line_off_len: int, prop_docs=False) -> str:
    formatted_docs = ''
    i = 0
    max_line_len = 79
    off = '    '
    multi_lines = False
    while i < len(docs):
        word_len = len(docs[i])
        if line_off_len + word_len > max_line_len:
            multi_lines = True
            line_indention = off + off
            if prop_docs:
                if multi_lines:
                    line_indention += off
                formatted_docs += '\n' + line_indention + docs[i] + ' '
                line_off_len = len(line_indention) + word_len + 1
            else:
                formatted_docs += '\n' + off + docs[i] + ' '
                line_off_len = len(off) + word_len + 1
        else:
            formatted_docs += docs[i] + ' '
            line_off_len += word_len + 1
        i += 1
    return formatted_docs


def format_doc(doc: str, indent: int = 4) -> str:
    if doc is None:
        return ''
    text = doc.strip()
    if text == '':
        return text

    # split the text into words
    words = []
    word = ''
    for char in text:
        if char.isspace():
            if len(word) > 0:
                words.append(word)
                word = ''
            continue
        word += char
    if len(word) > 0:
        words.append(word)

    text = ''
    line = ' ' * indent
    for word in words:
        if len(line) > indent:
            _line = line + ' ' + word
        else:
            _line = line + word
        if len(_line) > 79:
            text += line + '\n'
            line = ' ' * indent + word
        else:
            line = _line
    text += line

    return text


def has_prop_docs(c: model.ClassType) -> bool:
    has_docs = False
    for prop in c.properties:
        if len(prop.doc) > 0:
            return True
    return has_docs


def contains_link(doc: str) -> bool:
    return doc.count('</a>') > 0


def remove_link(doc: str) -> str:
    result = doc
    while result.count('</a>') > 0:
        link_prefix_idx = result.find('<a')
        link_close_idx = result.find('>')
        link_suffix_idx = result.find('</a>')
        if link_prefix_idx > 0 and link_close_idx > 0 and link_suffix_idx > 0:
            result = result[:link_prefix_idx - 1] + \
                     ' ' + result[link_close_idx + 1:link_suffix_idx] + \
                     result[link_suffix_idx + 4:]
    return result


if __name__ == '__main__':
    print('# This module contains a Python API of the JSON-LD based')
    print('# openLCA data exchange model.package schema.')
    print('# For more information see '
          'http://greendelta.github.io/olca-schema/\n')
    print('from enum import Enum')
    print('from typing import List, Optional\n')

    m = model.Model.load_yaml(YAML_DIR)  # type: model.Model
    for enum in m.enums:
        print_enum(enum)
    for clazz in m.classes:
        print_class(clazz, m)
