# Human-readable questions to Moodle XML converter

This repository provides a script that can be used to convert multi-choice
questions written in a (more) human-readable format to Moodle's XML format.

This repository is loosely based on work by @dandrei279 in
dandrei279/MXML-Converter.


## Expected format

Questions in the human-readable *must* contain three sections - *tags*,
*question* and *feedback*. Each section starts with a marker like `%section%`
and ends with a marker like `%~section%`. The lines with the markers cannot
contain any whitespaces - neither before or after the marker.

The `tags` section contains a list of tags that are attached to the question.
The list contains verbatim strings, separated by semicolons.

The `question` section contains the question text and possible answers for the
question. The question text starts on the first line and ends with the first
answer, either right or wrong. The answers start with either `+` or `-`,
to mark if the answer is correct or not. Like other markers, the `+` and `-`
signs cannot have leading spaces; if the `+` or `-` is lead by spaces, it is
considered part of the question text or the previous answer.

Note: Currently, a single correct answer is supported, and is marked with 100%
of the question's points.

The `feedback` section contains text that will be used as the question's general
feedback in Moodle.

Note: The question text, answers and feedback are parsed as markdown, so the
text enclosed in backticks, asterisks and underscores is emphasised in HTML as
expected. Code in triple backticks is converted to an image and is added as a
base-64 encoded PNG image file.

The following is an example of a question in human-readable format:

````
%tags%
easy;system-calls
%~tags%
%question%
When is using the `read` system call used?

The `read` wrapper function has the following prototype:

```
ssize_t read(int fd, void *buf, size_t count);
```
+ When fetching data from a file.
- When putting data into a file.
- When copying data between two pointers.
- When allocating memory.
%~question%
%feedback%
The `read` system call asks the operating system to fetch information from a
file and place it into the buffer passed as the second argument.
%~feedback%
````


## Requirements

The parser uses [lmxl](https://github.com/lxml/lxml) to output the questions to
an XML file, [Python-markdown](https://python-markdown.github.io/) to convert
the text from markdown to HTML and [pygments](http://pygments.org/) to convert
code snippets to images.


## Usage

To convert the questions in an `*.hr` file and write them to an XML file, run
the following command:

```bash
python3 hrparser.py -i questions.hr -o quiz.xml
```


## Limitations

The parser should be somewhat resilient to various format changes, but it is
recommended to always pay attention to details. For example, the delimiters that
are used to separate parts of the questions cannot have any whitespaces
before them (and also after them for the markers that start with `%`).

Also, a full question must *always* start with the `tags` section and end with
the `feedback` section, as the parser expects the first line of a question to be
`%tags` and the last line to be `%~feedback%`. This is mandatory since there is
no explicit marker that separates a full question's fields (including the
`tags`, `question` and `feedback` sections) from other questions.

Since `-` and `+` are used to mark the start of a wrong / right answer, neither
the question's text, or any of the answers can have `-` or `+` as the first
character of a line. If you want to have such characters in the text, add
a leading space before them.

The parsing of question parts is performed *before* any markdown conversions;
because of this, valid markers (not surrounded by whitespaces) cannot be used as
part of any text, even if some formatting (e.g., code snippets) may normally
imply escaping.


## Debugging

To debug what data the parser is matching, you can use the `to_dict` function on
any of the components of the quiz (including the quiz itself). The function
recursively converts member components to dictionaries using the same method.

To pretty-print the entire quiz's matches in JSON format, you can use the
following line:

```python
print(json.dumps(quiz.to_dict(), indent=4))
```
