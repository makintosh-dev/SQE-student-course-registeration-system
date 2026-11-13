import sys
import types
import re
import traceback

class RaisesContext:
    def __init__(self, expected_exc, match=None):
        self.expected_exc = expected_exc
        self.match = match
        self.value = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            raise AssertionError(f"Expected exception {self.expected_exc.__name__} was not raised")
        if not issubclass(exc_type, self.expected_exc):
            return False  # re-raise unexpected exception
        if self.match:
            msg = str(exc_val)
            if not re.search(self.match, msg):
                raise AssertionError(f"Pattern '{self.match}' did not match '{msg}'")
        self.value = exc_val
        return True

def mock_raises(expected_exc, match=None):
    return RaisesContext(expected_exc, match)

class MockMark:
    @staticmethod
    def parametrize(argnames, argvalues):
        def decorator(fn):
            fn._pytest_parametrize = (argnames, argvalues)
            return fn
        return decorator

# Install mock pytest module
mock_pytest = types.ModuleType("pytest")
mock_pytest.raises = mock_raises
mock_pytest.mark = MockMark()
sys.modules["pytest"] = mock_pytest

def run_tests_against(module_name, target_module_file):
    # Bind target module as 'registration'
    import importlib.util
    spec = importlib.util.spec_from_file_location("registration", target_module_file)
    reg_mod = importlib.util.module_from_spec(spec)
    sys.modules["registration"] = reg_mod
    spec.loader.exec_module(reg_mod)

    # Re-import test modules to bind new registration module
    for mod_name in list(sys.modules.keys()):
        if mod_name.startswith("tests."):
            del sys.modules[mod_name]

    import tests.test_blackbox as tbb
    import tests.test_whitebox as twb

    results = {"blackbox": {}, "whitebox": {}}

    def execute_test_suite(mod, key):
        suite_results = {}
        for attr_name in dir(mod):
            obj = getattr(mod, attr_name)
            # Standalone test functions
            if callable(obj) and attr_name.startswith("test_"):
                if hasattr(obj, "_pytest_parametrize"):
                    argnames, argvalues = obj._pytest_parametrize
                    for p_idx, p_val in enumerate(argvalues):
                        t_id = f"{attr_name}[case_{p_idx}]"
                        try:
                            if isinstance(p_val, (tuple, list)):
                                obj(*p_val)
                            else:
                                obj(p_val)
                            suite_results[t_id] = ("PASS", None)
                        except AssertionError as e:
                            suite_results[t_id] = ("FAIL", str(e))
                        except Exception as e:
                            suite_results[t_id] = ("ERROR", f"{type(e).__name__}: {str(e)}")
                else:
                    try:
                        obj()
                        suite_results[attr_name] = ("PASS", None)
                    except AssertionError as e:
                        suite_results[attr_name] = ("FAIL", str(e))
                    except Exception as e:
                        suite_results[attr_name] = ("ERROR", f"{type(e).__name__}: {str(e)}")

            # Test classes
            elif isinstance(obj, type) and attr_name.startswith("Test"):
                instance = obj()
                for method_name in dir(instance):
                    if method_name.startswith("test_"):
                        m = getattr(instance, method_name)
                        if callable(m):
                            if hasattr(m, "_pytest_parametrize"):
                                argnames, argvalues = m._pytest_parametrize
                                for p_idx, p_val in enumerate(argvalues):
                                    t_id = f"{attr_name}::{method_name}[case_{p_idx}]"
                                    try:
                                        if isinstance(p_val, (tuple, list)):
                                            m(*p_val)
                                        else:
                                            m(p_val)
                                        suite_results[t_id] = ("PASS", None)
                                    except AssertionError as e:
                                        suite_results[t_id] = ("FAIL", str(e))
                                    except Exception as e:
                                        suite_results[t_id] = ("ERROR", f"{type(e).__name__}: {str(e)}")
                            else:
                                t_id = f"{attr_name}::{method_name}"
                                try:
                                    m()
                                    suite_results[t_id] = ("PASS", None)
                                except AssertionError as e:
                                    suite_results[t_id] = ("FAIL", str(e))
                                except Exception as e:
                                    suite_results[t_id] = ("ERROR", f"{type(e).__name__}: {str(e)}")
        results[key] = suite_results

    execute_test_suite(tbb, "blackbox")
    execute_test_suite(twb, "whitebox")
    return results

print("=== Running tests against ORIGINAL registration.py ===")
orig_res = run_tests_against("registration", "registration.py")
bb_pass = sum(1 for status, _ in orig_res["blackbox"].values() if status == "PASS")
bb_fail = sum(1 for status, _ in orig_res["blackbox"].values() if status != "PASS")
wb_pass = sum(1 for status, _ in orig_res["whitebox"].values() if status == "PASS")
wb_fail = sum(1 for status, _ in orig_res["whitebox"].values() if status != "PASS")
print(f"Original registration.py Black-Box: {bb_pass} PASS, {bb_fail} FAIL (Total {len(orig_res['blackbox'])})")
print(f"Original registration.py White-Box: {wb_pass} PASS, {wb_fail} FAIL (Total {len(orig_res['whitebox'])})")

print("\n=== Running tests against FIXED registration_fixed.py ===")
fixed_res = run_tests_against("registration_fixed", "registration_fixed.py")
f_bb_pass = sum(1 for status, _ in fixed_res["blackbox"].values() if status == "PASS")
f_bb_fail = sum(1 for status, _ in fixed_res["blackbox"].values() if status != "PASS")
f_wb_pass = sum(1 for status, _ in fixed_res["whitebox"].values() if status == "PASS")
f_wb_fail = sum(1 for status, _ in fixed_res["whitebox"].values() if status != "PASS")
print(f"Fixed registration_fixed.py Black-Box: {f_bb_pass} PASS, {f_bb_fail} FAIL (Total {len(fixed_res['blackbox'])})")
print(f"Fixed registration_fixed.py White-Box: {f_wb_pass} PASS, {f_wb_fail} FAIL (Total {len(fixed_res['whitebox'])})")

if f_bb_fail > 0 or f_wb_fail > 0:
    print("\nFailing tests in fixed version:")
    for k, v in fixed_res["blackbox"].items():
        if v[0] != "PASS":
            print(f"  BB FAIL: {k} -> {v[1]}")
    for k, v in fixed_res["whitebox"].items():
        if v[0] != "PASS":
            print(f"  WB FAIL: {k} -> {v[1]}")
