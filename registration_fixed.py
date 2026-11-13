"""Student Course Registration System (Bug-Fixed Implementation).

Software Quality Engineering (SE3002) — Assignment 2
This module contains the corrected implementation of the registration system
derived from the authoritative functional specifications in REQUIREMENTS.md.

Original defects fixed:
- D-01: Dues check updated to block any balance > 0 (FR-04).
- D-02: Prerequisite check now requires all prerequisites to be completed (FR-03).
- D-03: Combined credit limit check now allows exactly 18 credits (<= 18) (FR-01).
- D-04: Full course check now correctly flags waitlisting when enrolled == capacity (FR-08).
- D-05: Course withdrawal now properly decrements enrolled student count (FR-13).
"""

from dataclasses import dataclass, field


@dataclass
class Student:
    """Represents a student enrolled in the university."""
    student_id: str
    completed_courses: set[str] = field(default_factory=set)
    current_credits: int = 0
    outstanding_dues: int = 0
    registered_courses: set[str] = field(default_factory=set)


@dataclass
class Course:
    """Represents an academic course offered in a semester."""
    code: str
    credit_hours: int
    capacity: int
    enrolled: int = 0
    prerequisites: set[str] = field(default_factory=set)
    waitlist: list[str] = field(default_factory=list)


def check_credit_limit(current_credits: int, new_credits: int) -> bool:
    """Check if adding new course credits stays within allowable credit load.
    
    FR-01: Total credits <= 18 is permitted (exactly 18 is allowed).
    FR-02: Validates current credits (0-18) and course credits (1-4).
    """
    if not 0 <= current_credits <= 18:
        raise ValueError("Invalid current credits")
    if not 1 <= new_credits <= 4:
        raise ValueError("Invalid course credits")
    
    # Defect D-03 Fix: was '< 18', now '<= 18' per FR-01
    return current_credits + new_credits <= 18


def prerequisites_satisfied(completed: set[str], required: set[str]) -> bool:
    """Return whether the student has completed all required prerequisites.
    
    FR-03: Returns True only if every required course is in completed courses.
           Returns True if required set is empty.
    """
    if not required:
        return True
    
    # Defect D-02 Fix: was 'completed.intersection(required)' (OR logic),
    # now requires every prerequisite to be completed (AND logic)
    return required.issubset(completed)


def registration_decision(student: Student, course: Course) -> str:
    """Evaluate registration eligibility without changing state.
    
    Evaluates business rules in strict priority order (FR-09):
    1. Validation guards (dues first, then course capacity/enrollment) (FR-15)
    2. Outstanding dues (> 0 blocks registration) (FR-04)
    3. Already registered duplicate check (FR-05)
    4. Prerequisites missing check (FR-06)
    5. Credit limit check (FR-07)
    6. Seat availability (WAITLISTED if full, else REGISTERED) (FR-08)
    """
    # Validation guards (FR-15) - checked in order: dues first, then capacity/enrolled
    if student.outstanding_dues < 0:
        raise ValueError("Invalid dues")
    if not 0 <= course.enrolled <= course.capacity or course.capacity < 1:
        raise ValueError("Invalid capacity or enrollment")
    
    # Defect D-01 Fix: was '> 1000', now '> 0' per FR-04
    if student.outstanding_dues > 0:
        return "DUES_BLOCK"
    
    # Duplicate registration check (FR-05)
    if course.code in student.registered_courses:
        return "ALREADY_REGISTERED"
    
    # Prerequisites check (FR-06)
    if not prerequisites_satisfied(student.completed_courses, course.prerequisites):
        return "PREREQUISITES_MISSING"
    
    # Credit limit check (FR-07)
    if not check_credit_limit(student.current_credits, course.credit_hours):
        return "CREDIT_LIMIT"
    
    # Defect D-04 Fix: was 'course.enrolled > course.capacity',
    # now checks if course is at capacity (enrolled >= capacity) per FR-08
    if course.enrolled >= course.capacity:
        return "WAITLISTED"
    
    return "REGISTERED"


def register_course(student: Student, course: Course) -> str:
    """Apply registration decision and update student and course records."""
    decision = registration_decision(student, course)
    
    if decision == "REGISTERED":
        student.registered_courses.add(course.code)
        student.current_credits += course.credit_hours
        course.enrolled += 1
    elif decision == "WAITLISTED" and student.student_id not in course.waitlist:
        course.waitlist.append(student.student_id)
        
    return decision


def withdraw_course(student: Student, course: Course) -> bool:
    """Withdraw an active registration and decrement course enrollment.
    
    FR-13: Removes course, subtracts credits, and decrements course enrollment.
    FR-14: Returns False if student not registered, with no state change.
    """
    if course.code not in student.registered_courses:
        return False
        
    student.registered_courses.remove(course.code)
    student.current_credits -= course.credit_hours
    
    # Defect D-05 Fix: decrement course enrollment count per FR-13
    course.enrolled -= 1
    
    return True
