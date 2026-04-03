
from xml.etree import ElementTree as etree

import markdown
from markdown.inlinepatterns import InlineProcessor
from markdown.util import AtomicString


class MathJaxPattern(InlineProcessor):
    def handleMatch(self, m, data):
        node = etree.Element("mathjax")
        node.text = AtomicString(f"{m.group(1)}{m.group(2)}{m.group(1)}")
        return node, m.start(0), m.end(0)


class MathJaxExtension(markdown.Extension):
    def extendMarkdown(self, md):
        # Needs to come before escape matching because \ is pretty important in LaTeX
        md.inlinePatterns.register(MathJaxPattern(r"(?<!\\)(\$\$?)(.+?)\1"), "mathjax", 185)

def makeExtension(**kwargs):
    return MathJaxExtension(**kwargs)


