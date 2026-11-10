import pytest
from registration import Student, Course, registration_decision

def student(**kw):
    data=dict(student_id="W001",completed_courses={"P1","P2"},current_credits=10,
              outstanding_dues=0,registered_courses=set())
    data.update(kw)
    return Student(**data)

def course(**kw):
    data=dict(code="C1",credit_hours=3,capacity=10,enrolled=5,
              prerequisites={"P1","P2"},waitlist=[])
    data.update(kw)
    return Course(**data)

# WB-01: negative-dues exception edge; WB-02: invalid-capacity exception edge.
def test_wb_negative_dues_validation():
    with pytest.raises(ValueError,match="Invalid dues"):
        registration_decision(student(outstanding_dues=-1),course())

def test_wb_invalid_capacity_validation():
    with pytest.raises(ValueError,match="Invalid capacity or enrollment"):
        registration_decision(student(),course(capacity=2,enrolled=3))

# WB-03..WB-08 exercise each ordered decision outcome and the final return.
@pytest.mark.parametrize("s,c,expected", [
    (student(outstanding_dues=1),course(),"DUES_BLOCK"),
    (student(registered_courses={"C1"}),course(),"ALREADY_REGISTERED"),
    (student(completed_courses=set()),course(),"PREREQUISITES_MISSING"),
    (student(current_credits=16),course(),"CREDIT_LIMIT"),
    (student(),course(enrolled=10),"WAITLISTED"),
    (student(),course(enrolled=9),"REGISTERED"),
])
def test_wb_decision_return_paths(s,c,expected):
    assert registration_decision(s,c) == expected

# WB-09..WB-12 isolate atomic predicates for condition analysis.
def test_wb_dues_zero_is_not_blocked():
    assert registration_decision(student(outstanding_dues=0),course()) == "REGISTERED"

def test_wb_duplicate_false():
    assert registration_decision(student(registered_courses=set()),course()) == "REGISTERED"

def test_wb_prerequisite_complete():
    assert registration_decision(student(completed_courses={"P1","P2"}),course()) == "REGISTERED"

def test_wb_credit_boundary_exactly_eighteen():
    assert registration_decision(student(current_credits=15),course(credit_hours=3)) == "REGISTERED"

def test_wb_seat_available_below_capacity():
    assert registration_decision(student(),course(enrolled=9,capacity=10)) == "REGISTERED"
