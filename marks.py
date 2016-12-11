import os
import re
from config import config

GRADE_REGEX = r" *#\+BEGIN_RESULT\n(?P<given>.*)/(?P<total>.*)\n *#\+END_RESULT"

class CombinedGrade:
    def __init__(self, normal=0, extra=0):
        self.normal = float(normal)
        self.extra = float(extra)

    @classmethod
    def from_string(cls, string):
        splitted = string.split('+')
        if len(splitted) <= 2:
            return cls(*splitted)

        normal, extra, rest = splitted
        if rest:
            raise ValueError("More than one separator: %s", string)
        return cls(normal, extra)

    def __eq__(self, other):
        return self.normal == other.normal and self.extra == other.extra

    def __iadd__(self, other):
        self.normal += other.normal
        self.extra += other.extra
        return self

    def __add__(self, other):
        return CombinedGrade(
            normal=self.normal + other.normal,
            extra=self.extra + other.extra,
        )
        
    def __repr__(self):
        if not self.extra:
            return '{}'.format(self.normal)
        return '{}+{}'.format(self.normal, self.extra)
    


def extract_grade_from_file(filename):
    with open(filename) as fd:
        content = fd.read()

    results = re.search(GRADE_REGEX, content)

    return {key: val.strip() for key, val in results.groupdict().items()}


def grades_of_person(person):
    for round_ in config.config_dict['rounds']:
        filename = os.path.join(person, round_, 'grading.org')
        try:
            yield round_, extract_grade_from_file(filename)
        except FileNotFoundError:
            continue

def grades_of_everyone():
    for person in config.config_dict['persons']:
        yield person, dict(grades_of_person(person))


def person_grade_sum(person):
    given, total = CombinedGrade(), CombinedGrade()
    for _, result in grades_of_person(person):
        given += CombinedGrade.from_string(result['given'])
        total += CombinedGrade.from_string(result['total'])
    return given, total
        

def grades_overview():
    for person in config.config_dict['persons']:
        given, total = person_grade_sum(person)
        print("{}: {} / {}".format(person, given, total))
