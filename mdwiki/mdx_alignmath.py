
from xml.etree import ElementTree as etree

import markdown
from markdown.inlinepatterns import InlineProcessor
from markdown.util import AtomicString


class AlignMathPattern(InlineProcessor):
    def handleMatch(self, m, data):
        node = etree.Element("mathjax")
        node.text = AtomicString(f"{m.group(1)}{m.group(2)}{m.group(3)}")
        return node, m.start(0), m.end(0)


class AlignMathExtension(markdown.Extension):
    def extendMarkdown(self, md):
        # Needs to come before escape matching because \ is pretty important in LaTeX
        md.inlinePatterns.register(
            AlignMathPattern(r"(\\begin\{align.*\})(.+?)(\\end\{align.*\})"),
            "alignmath",
            185,
        )

def makeExtension(**kwargs):
    return AlignMathExtension(**kwargs)
