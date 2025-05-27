"""
Convert questions from text format to Moodle XML
by Alexandru-Cristian Bardas
It takes in as a CLI argument the name of the file with the questions
It accepts both single-choice answers (displays radioboxes) and multiple-choice answers (displays checkboxes)
It also accepts essay-type questions (requires the "ANSWER:" line to be empty, as such, in order to work)
It randomly shuffles the answers
It invalidates a multiple-choice question if at least 1 incorrect answer is found
Input file format:
QUESTION TEXT (no empty lines)
A. AnswerA
B. AnswerB
....
G. AnswerG
ANSWER: A, C, E, G

QUESTION TEXT
....

The script splits the questions by \n\n, thus the requirement for no empty lines

Also, it transforms code sequences given in between <code> tags (as in HTML) to images with syntax highlighting according to the language, using the pygments library.

Example:
What will be the output of the following code?
<code lang="python">
def example():
    x = 5
    print(x * 2)
example()
</code>
A. 10
B. 5
C. 25
D. None
ANSWER: A

USAGE: <script> <quiz_bank_txt>
"""
import re
from pygments import highlight
from pygments.formatters import ImageFormatter
from pygments.lexers import get_lexer_by_name
from pygments.styles import get_style_by_name
import base64
import html
from PIL import Image
from pathlib import Path


def code_to_base64_image(code_snippet: str, language: str = 'python') -> str:
    try:
        lexer = get_lexer_by_name(language)
    except:
        lexer = get_lexer_by_name('text')

    formatter = ImageFormatter(
        style=get_style_by_name('monokai'),
        line_numbers=True,
        font_size=16,
        line_number_bg='#272822',
        line_number_fg='#8f908a',
        line_number_bold=True,
        font_name='Consolas'
    )
    img_data = highlight(code_snippet, lexer, formatter)
    base64_img = base64.b64encode(img_data).decode('utf-8')
    return base64_img


def process_question_text(text: str) -> str:
    def replace_code_block(match: re.Match) -> str:
        code = match.group(1)
        lang_match = re.match(r'<code\s+lang=["\']([^"\']+)["\']>', match.group(0))
        language = lang_match.group(1) if lang_match else 'python'
        code = html.unescape(code)
        base64_img = code_to_base64_image(code, language)
        return f'<img src="data:image/png;base64,{base64_img}" alt="Code snippet" />'
    
    text = re.sub(
        r'<code(?:\s+lang=["\'][^"\']+["\'])?>(.*?)</code>',
        replace_code_block, text,
        flags=re.DOTALL
    )
    return text


def extract_question_parts(question_text: str) -> tuple[str, list[str], list[str]]:
    parts = question_text.split('\n')
    question = []
    answers = []
    correct_answer = None
    in_answers = False
    
    for line in parts:
        if not line.strip():
            continue
        if line.strip().startswith('A.') or line.strip().startswith('ANSWER:'):
            in_answers = True
        if in_answers:
            if line.strip().startswith('ANSWER:'):
                correct_answer = line.strip().replace('ANSWER:', '').strip()
                correct_answer = [x.strip() for x in correct_answer.split(",")]
            else:
                match = re.match(r'([A-Z])\.\s*(.*)', line.strip())
                if match:
                    letter, text = match.groups()
                    answers.append((letter, text))
        else:
            question.append(line.rstrip())
    
    question_text = '\n'.join(question)
    question_text = process_question_text(question_text)
    return question_text, answers, correct_answer


def generate_moodle_xml(questions_text: str) -> str:
    questions = re.split(r'\n\s*\n', questions_text)
    questions = [q.strip('\n') for q in questions if q.strip()]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'
    
    for i, q in enumerate(questions, 1):
        if not q.strip():
            continue
        question_text, answers, correct_answer = extract_question_parts(q)
        question_text = question_text.replace('\t', '    ')
        question_text = f'<pre style="font-family: inherit;">{question_text}</pre>'
        if not answers:
            xml += f"""    <question type="essay">
        <name>
            <text>Quiz Question</text>
        </name>
        <questiontext format="html">
            <text><![CDATA[{question_text}]]></text>
        </questiontext>
        <generalfeedback format="html">
            <text></text>
        </generalfeedback>
        <defaultgrade>1</defaultgrade>
        <penalty>0</penalty>
        <hidden>0</hidden>
        <idnumber></idnumber>
        <responseformat>editor</responseformat>
        <responserequired>1</responserequired>
        <responsefieldlines>10</responsefieldlines>
        <minwordlimit></minwordlimit>
        <maxwordlimit></maxwordlimit>
        <attachments>0</attachments>
        <attachmentsrequired>0</attachmentsrequired>
"""
        else:
            xml += f"""    <question type="multichoice">
        <name>
            <text>Quiz Question</text>
        </name>
        <questiontext format="html">
            <text><![CDATA[{question_text}]]></text>
        </questiontext>
        <defaultgrade>1.0000000</defaultgrade>
        <hidden>0</hidden>
        <single>{"true" if len(correct_answer) == 1 else "false"}</single>
        <shuffleanswers>1</shuffleanswers>
        <answernumbering>none</answernumbering>
"""
            for letter, answer_text in answers:
                answer_text = process_question_text(answer_text)
                fraction = "{:.9f}".format(
                    100 / len(correct_answer)
                ) if letter in correct_answer else ("0" if len(correct_answer) == 1 else "-100")
                xml += f"""        <answer fraction="{fraction}">
            <text>{answer_text}</text>
        </answer>
"""
        xml += "    </question>\n\n"
    
    xml += "</quiz>"
    return xml


def main(filename: str) -> None:
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    xml = generate_moodle_xml(content)
    with open('moodle_quiz.xml', 'w', encoding='utf-8') as f:
        f.write(xml)


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Wrong usage! Usage: <script> <quiz_bank_file>")
        exit(1)
    if not Path(sys.argv[1]).is_file():
        print("Quiz bank file doesn't exist")
        exit(1)
    main(sys.argv[1])
