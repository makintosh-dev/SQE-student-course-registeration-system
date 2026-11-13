import pytest
from registration import Student, Course, check_credit_limit, prerequisites_satisfied, registration_decision, register_course, withdraw_course

def make_student(**kwargs):
    defaults = dict(student_id='S001', completed_courses={'CS101', 'MATH101'}, current_credits=12, outstanding_dues=0, registered_courses=set())
    defaults.update(kwargs)
    return Student(**defaults)

def make_course(**kwargs):
    defaults = dict(code='CS201', credit_hours=3, capacity=30, enrolled=10, prerequisites={'CS101', 'MATH101'}, waitlist=[])
    defaults.update(kwargs)
    return Course(**defaults)

class TestECP_CreditHoursClasses:

    def test_ecp01_valid_current_and_new_credits(self):
        result = check_credit_limit(10, 3)
        assert isinstance(result, bool)

    def test_ecp02_current_credits_below_zero(self):
        with pytest.raises(ValueError, match='Invalid current credits'):
            check_credit_limit(-1, 3)

    def test_ecp03_current_credits_above_max(self):
        with pytest.raises(ValueError, match='Invalid current credits'):
            check_credit_limit(19, 3)

    def test_ecp04_course_credits_below_one(self):
        with pytest.raises(ValueError, match='Invalid course credits'):
            check_credit_limit(10, 0)

    def test_ecp05_course_credits_above_four(self):
        with pytest.raises(ValueError, match='Invalid course credits'):
            check_credit_limit(10, 5)

class TestECP_DuesClasses:

    def test_ecp06_dues_zero_no_block(self):
        result = registration_decision(make_student(outstanding_dues=0), make_course())
        assert result == 'REGISTERED'

    def test_ecp07_dues_positive_block(self):
        result = registration_decision(make_student(outstanding_dues=500), make_course())
        assert result == 'DUES_BLOCK'

    def test_ecp08_dues_negative_raises(self):
        with pytest.raises(ValueError, match='Invalid dues'):
            registration_decision(make_student(outstanding_dues=-1), make_course())

class TestECP_PrerequisitesClasses:

    def test_ecp09_no_prerequisites_always_pass(self):
        assert prerequisites_satisfied(set(), set()) is True

    def test_ecp10_all_prerequisites_completed(self):
        assert prerequisites_satisfied({'CS101', 'MATH101'}, {'CS101', 'MATH101'}) is True

    def test_ecp11_some_prerequisites_missing(self):
        assert prerequisites_satisfied({'CS101'}, {'CS101', 'MATH101'}) is False

    def test_ecp12_no_courses_completed_prerequisites_required(self):
        assert prerequisites_satisfied(set(), {'CS101'}) is False

class TestBVA_CurrentCreditBoundaries:

    def test_bva01_current_credits_zero_min(self):
        assert check_credit_limit(0, 1) is True

    def test_bva02_current_credits_18_max(self):
        assert check_credit_limit(18, 1) is False

    def test_bva03_current_credits_minus_one_invalid(self):
        with pytest.raises(ValueError, match='Invalid current credits'):
            check_credit_limit(-1, 1)

    def test_bva04_current_credits_19_invalid(self):
        with pytest.raises(ValueError, match='Invalid current credits'):
            check_credit_limit(19, 1)

class TestBVA_CourseCreditsHoursBoundaries:

    def test_bva05_new_credits_one_min(self):
        assert check_credit_limit(10, 1) is True

    def test_bva06_new_credits_four_max(self):
        assert check_credit_limit(10, 4) is True

    def test_bva07_new_credits_zero_invalid(self):
        with pytest.raises(ValueError, match='Invalid course credits'):
            check_credit_limit(10, 0)

    def test_bva08_new_credits_five_invalid(self):
        with pytest.raises(ValueError, match='Invalid course credits'):
            check_credit_limit(10, 5)

class TestBVA_CombinedCreditLimit:

    def test_bva09_combined_exactly_18_allowed(self):
        assert check_credit_limit(15, 3) is True

    def test_bva10_combined_19_rejected(self):
        assert check_credit_limit(16, 3) is False

    def test_bva11_combined_17_allowed(self):
        assert check_credit_limit(14, 3) is True

class TestBVA_SeatAvailability:

    def test_bva12_enrolled_equals_capacity_waitlisted(self):
        s = make_student()
        c = make_course(enrolled=30, capacity=30)
        assert registration_decision(s, c) == 'WAITLISTED'

    def test_bva13_one_seat_remaining_registered(self):
        s = make_student()
        c = make_course(enrolled=29, capacity=30)
        assert registration_decision(s, c) == 'REGISTERED'

class TestBVA_DuesBoundary:

    def test_bva_dues_zero_not_blocked(self):
        assert registration_decision(make_student(outstanding_dues=0), make_course()) == 'REGISTERED'

    def test_bva_dues_one_blocked(self):
        assert registration_decision(make_student(outstanding_dues=1), make_course()) == 'DUES_BLOCK'

class TestDecisionTable:

    def test_dt01_all_conditions_false_registered(self):
        s = make_student(outstanding_dues=0, current_credits=12)
        c = make_course(enrolled=10, capacity=30)
        assert registration_decision(s, c) == 'REGISTERED'

    def test_dt02_dues_blocks_all(self):
        s = make_student(outstanding_dues=1, registered_courses={'CS201'}, completed_courses=set(), current_credits=18)
        c = make_course(enrolled=30, capacity=30)
        assert registration_decision(s, c) == 'DUES_BLOCK'

    def test_dt03_duplicate_registration(self):
        s = make_student(outstanding_dues=0, registered_courses={'CS201'})
        c = make_course()
        assert registration_decision(s, c) == 'ALREADY_REGISTERED'

    def test_dt04_prerequisites_missing(self):
        s = make_student(completed_courses=set())
        c = make_course()
        assert registration_decision(s, c) == 'PREREQUISITES_MISSING'

    def test_dt05_credit_limit_exceeded(self):
        s = make_student(current_credits=16)
        c = make_course(credit_hours=3)
        assert registration_decision(s, c) == 'CREDIT_LIMIT'

    def test_dt06_course_full_waitlisted(self):
        s = make_student(current_credits=12)
        c = make_course(enrolled=30, capacity=30)
        assert registration_decision(s, c) == 'WAITLISTED'

    def test_dt07_priority_duplicate_before_prerequisites(self):
        s = make_student(registered_courses={'CS201'}, completed_courses=set())
        c = make_course()
        assert registration_decision(s, c) == 'ALREADY_REGISTERED'

    def test_dt08_priority_prerequisites_before_credit_limit(self):
        s = make_student(completed_courses={'CS101'}, current_credits=18)
        c = make_course()
        assert registration_decision(s, c) == 'PREREQUISITES_MISSING'

    def test_dt09_priority_credit_limit_before_waitlist(self):
        s = make_student(current_credits=16)
        c = make_course(enrolled=30, capacity=30)
        assert registration_decision(s, c) == 'CREDIT_LIMIT'

    def test_dt10_dues_supersedes_credit_limit(self):
        s = make_student(outstanding_dues=1, current_credits=18)
        c = make_course()
        assert registration_decision(s, c) == 'DUES_BLOCK'

    def test_dt11_dues_supersedes_waitlist(self):
        s = make_student(outstanding_dues=100)
        c = make_course(enrolled=30, capacity=30)
        assert registration_decision(s, c) == 'DUES_BLOCK'

class TestStateChanges:

    def test_st01_successful_registration_updates_state(self):
        s = make_student(current_credits=12)
        c = make_course(enrolled=10, credit_hours=3)
        result = register_course(s, c)
        assert result == 'REGISTERED'
        assert 'CS201' in s.registered_courses, 'Course code must be added to registered_courses'
        assert s.current_credits == 15, 'Credits must increase by course credit_hours (3)'
        assert c.enrolled == 11, 'Course enrollment must increment by 1'

    def test_st02_successful_registration_no_waitlist_entry(self):
        s = make_student()
        c = make_course(enrolled=10)
        register_course(s, c)
        assert s.student_id not in c.waitlist

    def test_st03_waitlist_appends_student_once(self):
        s = make_student()
        c = make_course(enrolled=30, capacity=30)
        r1 = register_course(s, c)
        r2 = register_course(s, c)
        assert r1 == 'WAITLISTED'
        assert r2 == 'WAITLISTED'
        assert c.waitlist.count(s.student_id) == 1, 'Student ID must appear in waitlist exactly once'

    def test_st04_waitlist_no_credits_or_enrollment_change(self):
        s = make_student(current_credits=12)
        c = make_course(enrolled=30, capacity=30)
        credits_before = s.current_credits
        registered_before = set(s.registered_courses)
        enrolled_before = c.enrolled
        register_course(s, c)
        assert s.current_credits == credits_before
        assert s.registered_courses == registered_before
        assert c.enrolled == enrolled_before

    def test_st05_dues_block_no_state_change(self):
        s = make_student(outstanding_dues=500)
        c = make_course(enrolled=10)
        credits_before = s.current_credits
        registered_before = set(s.registered_courses)
        enrolled_before = c.enrolled
        waitlist_before = list(c.waitlist)
        result = register_course(s, c)
        assert result == 'DUES_BLOCK'
        assert s.current_credits == credits_before
        assert s.registered_courses == registered_before
        assert c.enrolled == enrolled_before
        assert c.waitlist == waitlist_before

    def test_st06_already_registered_no_state_change(self):
        s = make_student(registered_courses={'CS201'}, current_credits=12)
        c = make_course(enrolled=10)
        credits_before = s.current_credits
        registered_before = set(s.registered_courses)
        enrolled_before = c.enrolled
        result = register_course(s, c)
        assert result == 'ALREADY_REGISTERED'
        assert s.current_credits == credits_before
        assert s.registered_courses == registered_before
        assert c.enrolled == enrolled_before

    def test_st07_prerequisites_missing_no_state_change(self):
        s = make_student(completed_courses=set())
        c = make_course(enrolled=10)
        credits_before = s.current_credits
        registered_before = set(s.registered_courses)
        enrolled_before = c.enrolled
        result = register_course(s, c)
        assert result == 'PREREQUISITES_MISSING'
        assert s.current_credits == credits_before
        assert s.registered_courses == registered_before
        assert c.enrolled == enrolled_before

    def test_st08_credit_limit_no_state_change(self):
        s = make_student(current_credits=16)
        c = make_course(enrolled=10)
        credits_before = s.current_credits
        registered_before = set(s.registered_courses)
        enrolled_before = c.enrolled
        result = register_course(s, c)
        assert result == 'CREDIT_LIMIT'
        assert s.current_credits == credits_before
        assert s.registered_courses == registered_before
        assert c.enrolled == enrolled_before

    def test_st09_withdrawal_updates_state(self):
        s = make_student(registered_courses={'CS201'}, current_credits=15)
        c = make_course(enrolled=11, credit_hours=3)
        result = withdraw_course(s, c)
        assert result is True
        assert 'CS201' not in s.registered_courses, 'Course must be removed from registered_courses'
        assert s.current_credits == 12, 'Credits must decrease by course credit_hours (3)'
        assert c.enrolled == 10, 'Course enrollment must decrement by 1 (FR-13)'

    def test_st10_withdrawal_not_registered_no_change(self):
        s = make_student()
        c = make_course(enrolled=10)
        credits_before = s.current_credits
        registered_before = set(s.registered_courses)
        enrolled_before = c.enrolled
        result = withdraw_course(s, c)
        assert result is False
        assert s.current_credits == credits_before
        assert s.registered_courses == registered_before
        assert c.enrolled == enrolled_before

class TestInputValidation:

    def test_negative_dues_raises_before_capacity(self):
        with pytest.raises(ValueError, match='Invalid dues'):
            registration_decision(make_student(outstanding_dues=-1), make_course(capacity=0))

    @pytest.mark.parametrize('capacity,enrolled', [(0, 0), (3, -1), (3, 4)])
    def test_invalid_capacity_or_enrollment_raises(self, capacity, enrolled):
        with pytest.raises(ValueError, match='Invalid capacity or enrollment'):
            registration_decision(make_student(), make_course(capacity=capacity, enrolled=enrolled))

    def test_error_check_order_current_before_new_credits(self):
        with pytest.raises(ValueError, match='Invalid current credits'):
            check_credit_limit(-1, 0)
