from parts import *

import argparse
from lxml import etree as ElementTree
import json


class HRParser:
	def __init__(self, infile: str, outfile: str):
		self.infile = infile
		self.outfile = outfile


	def parse(self):
		with open(self.infile, "r") as f:
			fcontent = f.read()

		quiz = Quiz()
		quiz.match(fcontent)
		quiz_elem = quiz.to_xml()

		ElementTree.indent(quiz_elem)
		xml_tree = ElementTree.ElementTree(quiz_elem)
		xml_tree.write(self.outfile, encoding="UTF-8", xml_declaration=True)


if __name__ == "__main__":
	argparser = argparse.ArgumentParser(description="Human-readable questions file to MXML coverter")
	argparser.add_argument("--infile", "-i", help="File to parse", required=True)
	argparser.add_argument("--output", "-o", help="Output file name", required=True)

	args = argparser.parse_args()

	hrparser = HRParser(args.infile, args.output)
	hrparser.parse()
