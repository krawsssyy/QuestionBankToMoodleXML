# QuestionBankToMoodleXML

Small Python script to convert questions from TXT format into Moodle XML for ease of upload as question banks.

Allows for insertion of code in the question, via <code> tags (requires specification of language), as in HTML by using `pygments` and `pillow` libraries.
It allows for single-choice questions (single answer - denoted by radioboxes) and multiple-choice questions (multiple answers - denoted by checkboxes). This is determined automatically by the number of answers.

It displays no numbering on the questions and shuffles the answers. A single wrong option on the multiple-choice questions invalidates the question, making it 0 points.

Question Bank TXT format is as follows:

QUESTION TEXT
A. AnswerA
B. AnswerB
C. AnswerC
D. AnswerD
ANSWER: A, C

QUESTION TEXT
....

Questions are split by `\n\n`, so please ensure there's no empty newlines in other places.
