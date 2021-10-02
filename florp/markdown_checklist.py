import re
import xml.etree.ElementTree as ET

from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

item_pattern = re.compile(r'^\[([ Xx])\](.*)$', re.MULTILINE)


class CheckboxExtension(Extension):
    def extendMarkdown(self, md):
        md.treeprocessors.register(CheckboxTreeProcessor(), 'checklist', 9999)


class CheckboxTreeProcessor(Treeprocessor):
    def run(self, root) -> None:
        for el in root.iter('li'):
            match = item_pattern.match(el.text)
            if match:
                check = ET.Element('input')
                check.attrib = {'type': 'checkbox', 'disabled': ''}
                if match[1].lower() == 'x':
                    check.attrib['checked'] = ''
                el.insert(0, check)
                el.text = None
                check.tail = match[2]