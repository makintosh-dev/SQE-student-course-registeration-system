import pytest
from registration import Student, Course, registration_decision, register_course, check_credit_limit, prerequisites_satisfied

def student(**kw):
    data = dict(student_id='W001', completed_courses={'P1', 'P2'}, current_credits=10, outstanding_dues=0, registered_courses=set())
    data.update(kw)
    return Student(**data)

def course(**kw):
    data = dict(code='C1', credit_hours=3, capacity=10, enrolled=5, prerequisites={'P1', 'P2'}, waitlist=[])
    data.update(kw)
    return Course(**data)

class _DynamicEnrollmentCourse(Course):

    def __init__(self, first_enrolled: int, second_enrolled: int, **kw):
        super().__init__(**kw)
        self._reads = iter([first_enrolled, second_enrolled])
        object.__setattr__(self, 'enrolled', first_enrolled)

    @property
    def enrolled(self):
        try:
            return next(self._reads)
        except StopIteration:
            return 0

    @enrolled.setter
    def enrolled(self, value):
        pass

def test_wb01_negative_dues_raises_value_error():
    with pytest.raises(ValueError, match='Invalid dues'):
        registration_decision(student(outstanding_dues=-1), course())

def test_wb02_enrolled_below_zero_raises():
    with pytest.raises(ValueError, match='Invalid capacity or enrollment'):
        registration_decision(student(), course(enrolled=-1, capacity=10))

def test_wb02b_enrolled_above_capacity_raises():
    with pytest.raises(ValueError, match='Invalid capacity or enrollment'):
        registration_decision(student(), course(enrolled=11, capacity=10))

def test_wb02c_capacity_below_one_raises():
    with pytest.raises(ValueError, match='Invalid capacity or enrollment'):
        registration_decision(student(), course(enrolled=0, capacity=0))

@pytest.mark.parametrize('s,c,expected', [(student(outstanding_dues=1), course(), 'DUES_BLOCK'), (student(registered_courses={'C1'}), course(), 'ALREADY_REGISTERED'), (student(completed_courses=set()), course(), 'PREREQUISITES_MISSING'), (student(current_credits=16), course(), 'CREDIT_LIMIT'), (student(), course(enrolled=10), 'WAITLISTED'), (student(), course(enrolled=9), 'REGISTERED')])
def test_wb_decision_return_paths(s, c, expected):
    assert registration_decision(s, c) == expected

def test_wb09_dues_zero_not_blocked():
    assert registration_decision(student(outstanding_dues=0), course()) == 'REGISTERED'

def test_wb10_not_already_registered():
    assert registration_decision(student(registered_courses=set()), course()) == 'REGISTERED'

def test_wb11_prerequisites_fully_met():
    assert registration_decision(student(completed_courses={'P1', 'P2'}), course()) == 'REGISTERED'

def test_wb12_credit_boundary_exactly_eighteen():
    assert registration_decision(student(current_credits=15), course(credit_hours=3)) == 'REGISTERED'

def test_wb12b_credit_well_within_limit():
    assert registration_decision(student(current_credits=10), course(credit_hours=3)) == 'REGISTERED'

def test_wb12c_credit_one_below_limit():
    assert registration_decision(student(current_credits=14), course(credit_hours=3)) == 'REGISTERED'

def test_wb12d_seat_available_below_capacity():
    assert registration_decision(student(), course(enrolled=9, capacity=10)) == 'REGISTERED'

def test_wb13_dues_above_1000_causes_dues_block():
    s = student(outstanding_dues=1001)
    result = registration_decision(s, course())
    assert result == 'DUES_BLOCK'

def test_wb14_waitlisted_branch_line59():
    dynamic = _DynamicEnrollmentCourse(first_enrolled=5, second_enrolled=11, code='C1', credit_hours=3, capacity=10, prerequisites=set(), waitlist=[])
    s = student(completed_courses=set())
    result = registration_decision(s, dynamic)
    assert result == 'WAITLISTED'

def test_wb15_register_course_waitlist_appends_new_student():
    dynamic = _DynamicEnrollmentCourse(first_enrolled=5, second_enrolled=11, code='C1', credit_hours=3, capacity=10, prerequisites=set(), waitlist=[])
    s = student(completed_courses=set())
    result = register_course(s, dynamic)
    assert result == 'WAITLISTED'
    assert 'W001' in dynamic.waitlist

def test_wb16_register_course_no_duplicate_on_waitlist():
    dynamic = _DynamicEnrollmentCourse(first_enrolled=5, second_enrolled=11, code='C1', credit_hours=3, capacity=10, prerequisites=set(), waitlist=['W001'])
    s = student(completed_courses=set())
    result = register_course(s, dynamic)
    assert result == 'WAITLISTED'
    assert dynamic.waitlist.count('W001') == 1

def test_wb17_mcdc_prereqs_empty_required_always_true():
    assert prerequisites_satisfied(set(), set()) is True

def test_wb18_mcdc_prereqs_nonempty_required_not_met():
    assert prerequisites_satisfied(set(), {'P1'}) is False

def test_wb19_mcdc_prereqs_nonempty_required_fully_met():
    assert prerequisites_satisfied({'P1'}, {'P1'}) is True

def test_wb20_dues_validation_precedes_capacity_check():
    with pytest.raises(ValueError, match='Invalid dues'):
        registration_decision(student(outstanding_dues=-1), course(capacity=0, enrolled=0))
