import base64
from lxml import etree as ElementTree
import markdown
import pygments
import pygments.lexers
from pygments.formatters import ImageFormatter
import random
import re
import string


class QuizPart:
	def __init__(self, start: str = "", end: str = "", members: set = {},
				fullmatch: bool = False, greedy: bool = False):
		self.start = start
		self.end = end
		self.members = members
		self.fullmatch = fullmatch
		self.greedy = greedy
		self.text = None

		self.membermap = {}
		for m in self.members:
			self.membermap[m] = []


	def match(self, data: str) -> str:
		if self.greedy:
			regex = f"(?P<start>{self.start})\s*(?P<text>.*)\s*(?P<end>{self.end})"
		else:
			regex = f"(?P<start>{self.start})\s*(?P<text>.*?)\s*(?P<end>{self.end})"

		tc = re.search(regex, data, re.MULTILINE | re.DOTALL)
		if tc is None:
			return ""

		if self.fullmatch:
			text = tc.group(0) # Use all text as the matched value
		else:
			text = tc.group("text")

		self.text = text.strip()

		for cls in self.members:
			while True:
				member = cls()
				match = member.match(text)
				if match == "":
					break

				self.membermap[cls].append(member)
				text = text.replace(match, "")

		# Return the entire match so it can be removed from the data input
		# in the parsing level above
		return tc.group(0)


	def to_dict(self):
		res = {}

		res["type"] = str(type(self))
		res["text"] = self.text
		res["membermap"] = {}

		for cls in self.members:
			res["membermap"][str(cls)] = []

			for member in self.membermap[cls]:
				res["membermap"][str(cls)].append(member.to_dict())

		return res


	def __str__(self) -> str:
		return str(self.to_dict())


	def get_members_xmls(self) -> list:
		elems = []

		for cls in self.members:
			for member in self.membermap[cls]:
				xml = member.to_xml()

				if type(xml) == list:
					elems += xml
				else:
					elems += [xml]

		return elems


	def text_to_html(self):
		image_map = {}
		text = self.text

		code_regex = "\s*```(?P<dialect>\w*)\s*(?P<code>.*?)\s*```"

		while True:
			tc = re.search(code_regex, text, re.MULTILINE | re.DOTALL)

			if tc is None:
				break

			dialect = tc.group("dialect").lower()
			code = tc.group("code")

			if dialect == "c":
				lexer = pygments.lexers.CLexer()
			elif dialect == "d":
				lexer = pygments.lexers.DLexer()
			elif dialect == "python":
				lexer = pygments.lexers.PythonLexer()
			elif dialect == "bash":
				lexer = pygments.lexers.BashLexer()
			else:
				lexer = pygments.lexers.CLexer()

			# Generate a random ID to keep track of the generated (code) image in a dictionary
			image_id = "".join([random.choice(string.ascii_letters + string.digits) for _ in range(50)])

			image = pygments.highlight(code, lexer, ImageFormatter())
			image_b64 = base64.b64encode(image)

			image_map[image_id] = image_b64

			# Replace the image with a marker to avoid interfering
			# with the markdown paraser
			text = text.replace(tc.group(0), f"\n\n{image_id}\n\n")

		# Convert the string from markdown to HTML
		html = markdown.markdown(text)

		# Replace the image markers with the actual images
		for image_id, image_b64 in image_map.items():
			html = html.replace(image_id, f"<img src=\"data:image/png;base64, {image_b64.decode('ascii')}\"/>")

		return html


class Quiz(QuizPart):
	def __init__(self):
		super().__init__(members={QuizItem}, greedy=True)


	def to_xml(self) -> ElementTree.Element:
		elem = ElementTree.Element("quiz")

		elem.extend(self.get_members_xmls())

		return elem


class QuizItem(QuizPart):
	def __init__(self):
		super().__init__(start="(^%tags%$)", end="(^%~feedback%$)",
				members={Tags, Question, Feedback}, fullmatch=True)


	def to_xml(self) -> ElementTree.Element:
		elem = ElementTree.Element("question", type="multichoice")

		questiontext = self.membermap[Question][0].membermap[QuestionText][0].text
		# Extract part of the text to use as the name
		questiontext = re.sub("\s+", " ", questiontext)
		questiontext = re.sub("[*`_]", "", questiontext)

		nameelem = ElementTree.Element("name")
		text = questiontext[:35].strip()
		if text != questiontext:
			text += "..."
		ElementTree.SubElement(nameelem, "text").text = text
		elem.append(nameelem)

		ElementTree.SubElement(elem, "defaultgrade").text = "1.000000"
		ElementTree.SubElement(elem, "penalty").text = "0.3333333"
		ElementTree.SubElement(elem, "hidden").text = "0"
		ElementTree.SubElement(elem, "idnumber")
		ElementTree.SubElement(elem, "single").text = "true"
		ElementTree.SubElement(elem, "shuffleanswers").text = "true"
		ElementTree.SubElement(elem, "answernumbering").text = "abc"
		ElementTree.SubElement(elem, "showstandardinstruction").text = "0"

		answerfeedback = ElementTree.Element("correctfeedback", format="html")
		ElementTree.SubElement(answerfeedback, "text").text = "Your answer is correct."
		elem.append(answerfeedback)

		answerfeedback = ElementTree.Element("partiallycorrectfeedback", format="html")
		ElementTree.SubElement(answerfeedback, "text").text = "Your answer is partially correct."
		elem.append(answerfeedback)

		answerfeedback = ElementTree.Element("incorrectfeedback", format="html")
		ElementTree.SubElement(answerfeedback, "text").text = "Your answer is incorrect."
		elem.append(answerfeedback)

		ElementTree.SubElement(elem, "shownumcorrect")

		elem.extend(self.get_members_xmls())

		return elem


class Tags(QuizPart):
	def __init__(self):
		super().__init__(start="^%tags%$", end="^%~tags%$")


	def to_xml(self) -> ElementTree.Element:
		elem = ElementTree.Element("tags")

		for tag in self.text.split(";"):
			tagelem = ElementTree.Element("tag")
			ElementTree.SubElement(tagelem, "text").text = tag.strip()
			elem.append(tagelem)

		return elem


class Question(QuizPart):
	def __init__(self):
		super().__init__(start="^%question%$", end="^%~question%$",
				members={QuestionText, QuestionAnswerRight, QuestionAnswerWrong})


	def to_xml(self) -> list:
		return self.get_members_xmls()


class QuestionText(QuizPart):
	def __init__(self):
		super().__init__(start="\A\s*", end="(?=^[-+]|\Z)")


	def to_xml(self) -> ElementTree.Element:
		elem = ElementTree.Element("questiontext", format="html")

		html = self.text_to_html()
		ElementTree.SubElement(elem, "text").text = ElementTree.CDATA(html)

		return elem


class QuestionAnswer(QuizPart):
	def __init__(self, points: int, **kwargs):
		super().__init__(**kwargs)
		self.points = points


	def to_xml(self) -> ElementTree.Element:
		elem = ElementTree.Element("answer", fraction=str(self.points), format="html")

		html = self.text_to_html()
		ElementTree.SubElement(elem, "text").text = ElementTree.CDATA(html)

		feedbackelem = ElementTree.Element("feedback", format="html")
		ElementTree.SubElement(feedbackelem, "text")

		elem.append(feedbackelem)

		return elem


class QuestionAnswerRight(QuestionAnswer):
	def __init__(self):
		super().__init__(start="^\+", end="(?=^[-+]|\Z)", points=100)


class QuestionAnswerWrong(QuestionAnswer):
	def __init__(self):
		super().__init__(start="^\-", end="(?=^[-+]|\Z)", points=0)


class Feedback(QuizPart):
	def __init__(self):
		super().__init__(start="^%feedback%$", end="^%~feedback%$")


	def to_xml(self) -> ElementTree.Element:
		elem = ElementTree.Element("generalfeedback", format="html")

		html = self.text_to_html()
		ElementTree.SubElement(elem, "text").text = ElementTree.CDATA(html)

		return elem
