import pytest
from registration import Student, Course, check_credit_limit, prerequisites_satisfied, registration_decision, register_course, withdraw_course

# ECP-01..08 and BVA-01..10: expected results are derived from REQUIREMENTS.md.
@pytest.mark.parametrize("current,new,expected", [
    (0,1,True), (14,4,True), (15,3,True), (16,3,False),
    (18,1,False), (0,4,True), (17,1,True), (17,2,False),
])
def test_credit_limit_valid_partitions_and_boundaries(current,new,expected):
    assert check_credit_limit(current,new) is expected

@pytest.mark.parametrize("current,new,message", [
    (-1,1,"Invalid current credits"), (19,1,"Invalid current credits"),
    (0,0,"Invalid course credits"), (0,5,"Invalid course credits"),
])
def test_credit_limit_invalid_partitions(current,new,message):
    with pytest.raises(ValueError, match=message):
        check_credit_limit(current,new)

@pytest.mark.parametrize("completed,required,expected", [
    (set(),set(),True),
    ({"CS101"},{"CS101"},True),
    ({"CS101","MATH101"},{"CS101","MATH101"},True),
    ({"CS101"},{"CS101","MATH101"},False),
    (set(),{"CS101"},False),
])
def test_prerequisite_equivalence_classes(completed,required,expected):
    assert prerequisites_satisfied(completed,required) is expected

def make_student(**kwargs):
    values = dict(student_id="S001", completed_courses={"CS101","MATH101"},
                  current_credits=12, outstanding_dues=0, registered_courses=set())
    values.update(kwargs)
    return Student(**values)

def make_course(**kwargs):
    values = dict(code="CS201", credit_hours=3, capacity=30, enrolled=10,
                  prerequisites={"CS101","MATH101"}, waitlist=[])
    values.update(kwargs)
    return Course(**values)

# Decision outcomes and priority combinations.
@pytest.mark.parametrize("student,course,expected", [
    (make_student(outstanding_dues=1), make_course(), "DUES_BLOCK"),
    (make_student(registered_courses={"CS201"}), make_course(), "ALREADY_REGISTERED"),
    (make_student(completed_courses={"CS101"}), make_course(), "PREREQUISITES_MISSING"),
    (make_student(current_credits=16), make_course(), "CREDIT_LIMIT"),
    (make_student(), make_course(enrolled=30), "WAITLISTED"),
    (make_student(), make_course(enrolled=29), "REGISTERED"),
])
def test_decision_table_distinct_outcomes(student,course,expected):
    assert registration_decision(student,course) == expected

def test_decision_priority_dues_before_all_other_blocks():
    s=make_student(outstanding_dues=1,registered_courses={"CS201"},completed_courses=set(),current_credits=18)
    assert registration_decision(s,make_course(enrolled=30)) == "DUES_BLOCK"

def test_decision_priority_duplicate_before_prerequisite():
    s=make_student(registered_courses={"CS201"},completed_courses=set())
    assert registration_decision(s,make_course()) == "ALREADY_REGISTERED"

def test_decision_priority_prerequisite_before_credit_limit():
    s=make_student(completed_courses={"CS101"},current_credits=18)
    assert registration_decision(s,make_course()) == "PREREQUISITES_MISSING"

# State transition tests.
def test_successful_registration_updates_all_state():
    s=make_student(current_credits=12)
    c=make_course(enrolled=10)
    assert register_course(s,c) == "REGISTERED"
    assert "CS201" in s.registered_courses
    assert s.current_credits == 15
    assert c.enrolled == 11

def test_waitlist_adds_student_once_without_other_state_changes():
    s=make_student()
    c=make_course(enrolled=30)
    before=(s.current_credits,set(s.registered_courses),c.enrolled)
    assert register_course(s,c) == "WAITLISTED"
    assert c.waitlist == ["S001"]
    assert (s.current_credits,s.registered_courses,c.enrolled) == before
    assert register_course(s,c) == "WAITLISTED"
    assert c.waitlist == ["S001"]

@pytest.mark.parametrize("student,course", [
    (make_student(outstanding_dues=1),make_course()),
    (make_student(registered_courses={"CS201"}),make_course()),
    (make_student(completed_courses=set()),make_course()),
    (make_student(current_credits=16),make_course()),
])
def test_unsuccessful_registration_does_not_change_state(student,course):
    before=(set(student.registered_courses),student.current_credits,course.enrolled,list(course.waitlist))
    register_course(student,course)
    assert (student.registered_courses,student.current_credits,course.enrolled,course.waitlist) == before

def test_withdrawal_removes_course_and_updates_credits_and_enrollment():
    s=make_student(registered_courses={"CS201"},current_credits=15)
    c=make_course(enrolled=11)
    assert withdraw_course(s,c) is True
    assert "CS201" not in s.registered_courses
    assert s.current_credits == 12
    assert c.enrolled == 10

def test_withdrawal_of_unregistered_course_changes_nothing():
    s=make_student()
    c=make_course(enrolled=10)
    before=(set(s.registered_courses),s.current_credits,c.enrolled)
    assert withdraw_course(s,c) is False
    assert (s.registered_courses,s.current_credits,c.enrolled) == before

# Numeric validation and validation order.
def test_negative_dues_raise_value_error():
    with pytest.raises(ValueError,match="Invalid dues"):
        registration_decision(make_student(outstanding_dues=-1),make_course())

@pytest.mark.parametrize("capacity,enrolled", [(0,0),(3,-1),(3,4)])
def test_invalid_capacity_or_enrollment_raises(capacity,enrolled):
    with pytest.raises(ValueError,match="Invalid capacity or enrollment"):
        registration_decision(make_student(),make_course(capacity=capacity,enrolled=enrolled))

def test_dues_validation_precedes_capacity_validation():
    with pytest.raises(ValueError,match="Invalid dues"):
        registration_decision(make_student(outstanding_dues=-1),make_course(capacity=0))
