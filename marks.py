import os
import re
from config import config
from operator import itemgetter

GRADE_REGEX = r" *#\+BEGIN_RESULT\n(?P<given>.*)/(?P<total>.*)\n *#\+END_RESULT"

class CombinedGrade:
    def __init__(self, normal=0, extra=0):
        self.normal = float(normal)
        self.extra = float(extra)

    @classmethod
    def from_string(cls, string):
        splitted = string.split('+')
        if len(splitted) <= 2:
            return cls(*(x or 0 for x in splitted))

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

    def __rsub__(self, other):
        # we can assert that the other operand isn't a
        # `CombinedGrade`, else it would supprt addition
        return other - float(self)

    def __sub__(self, other):
        try:
            return CombinedGrade(
                normal=self.normal - other.normal,
                extra=self.extra - other.extra,
            )
        except AttributeError:
            return float(self) - other

    def __le__(self, other):
        try:
            return self.normal <= other.normal and self.extra <= other.extra
        except AttributeError:
            return float(self) <= other

    def __lt__(self, other):
        try:
            return self.normal < other.normal and self.extra < other.extra
        except AttributeError:
            return float(self) < other

    def __float__(self):
        return self.normal + self.extra

    def __rsub__(self, other):
        # we can assert that the other operand isn't a
        # `CombinedGrade`, else it would supprt addition
        return other - float(self)

    def __sub__(self, other):
        try:
            return CombinedGrade(
                normal=self.normal - other.normal,
                extra=self.extra - other.extra,
            )
        except AttributeError:
            return float(self) - other

    def __le__(self, other):
        try:
            return self.normal <= other.normal and self.extra <= other.extra
        except AttributeError:
            return float(self) <= other

    def __lt__(self, other):
        try:
            return self.normal < other.normal and self.extra < other.extra
        except AttributeError:
            return float(self) < other

    def __float__(self):
        return self.normal + self.extra

    def __repr__(self):
        if not self.extra:
            return '{}'.format(self.normal)
        return '{}+{}'.format(self.normal, self.extra)

    def __format__(self, spec):
        return str(self).__format__(spec)


def extract_grade_from_file(filename):
    with open(filename) as fd:
        content = fd.read()

    results = re.search(GRADE_REGEX, content)

    return {key: CombinedGrade.from_string(val.strip())
            for key, val in results.groupdict().items()}


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
        given += result['given']
        total += result['total']
    return given, total


NEEDED = 78
EXERCISES_NEEDED = 9
# STILL_AHEAD = 7

CELL_WIDTH = 20
CELL_FMT = "{{: <{width}}}".format(width=CELL_WIDTH)

def person_overview(person):
    """Build a formatted overview of a person's grades"""
    overview = ''

    overview += "Grades for person '{}'\n".format(person)

    all_grades = ((round_, grade['given'], grade['total'])
                  for round_, grade in grades_of_person(person))
    all_grades = sorted(all_grades, key=itemgetter(0))

    overview += "\n{header}\n{blank:-<{width}}\n".format(
        header=''.join(CELL_FMT.format(x) for x in ("Round", "Given", "Total")),
        width=CELL_WIDTH*3,
        blank='',
    )

    for tuple_ in all_grades:
        overview += ''.join(CELL_FMT.format(item) for item in tuple_)
        overview += '\n'

    sum_gotten = sum((x[1] for x in all_grades), CombinedGrade(0))
    sum_total = sum((x[2] for x in all_grades), CombinedGrade(0))

    overview += '\n'
    overview += "You got {} out of (currently) {} points.\n".format(sum_gotten, sum_total)
    if sum_gotten < NEEDED:
        overview += "You are missing {} points to reach the {} point passing barrier.\n"\
                    .format(NEEDED - sum_gotten, NEEDED)
    else:
        overview += "You surpassed the {} point passing barrier by {} points.\n"\
                    .format(NEEDED, sum_gotten - NEEDED)
    overview += "You sent in {} out of {} necessary exercises.\n"\
                .format(sum(bool(x[1]) for x in all_grades), EXERCISES_NEEDED)
    return overview


def grades_overview(person=None, *a, **kw):
    if person:
        print(person_overview(person, *a, **kw))
        exit(0)

    for person in config.config_dict['persons']:
        given, total = person_grade_sum(person)
        missing = NEEDED - float(given)
        print("{}: {} / {} ({} missing)".format(person, given, total, missing))
