from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

from unittest import TestCase
from unittest.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes


def set_module_args(args):
    """Set module arguments for testing"""
    if args is None:
        args = {}
    
    if "_ansible_remote_tmp" not in args:
        args["_ansible_remote_tmp"] = "/tmp"
    if "_ansible_keep_remote_files" not in args:
        args["_ansible_keep_remote_files"] = False
    
    args_json = json.dumps({"ANSIBLE_MODULE_ARGS": args})
    basic._ANSIBLE_ARGS = to_bytes(args_json)


class AnsibleExitJson(Exception):
    """Exception to simulate module.exit_json()"""
    pass


class AnsibleFailJson(Exception):
    """Exception to simulate module.fail_json()"""
    pass


def exit_json(*args, **kwargs):
    """Mock for AnsibleModule.exit_json"""
    if "changed" not in kwargs:
        kwargs["changed"] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    """Mock for AnsibleModule.fail_json"""
    kwargs["failed"] = True
    raise AnsibleFailJson(kwargs)


class ModuleTestCase(TestCase):
    """Base test case class for Junos collection modules"""

    def setUp(self):
        """Set up test fixtures"""
        # Mock exit_json and fail_json
        self.mock_module = patch.multiple(
            'ansible.module_utils.basic.AnsibleModule',
            exit_json=exit_json,
            fail_json=fail_json,
        )
        self.mock_module.start()

        # Mock time.sleep to speed up tests
        self.mock_sleep = patch("time.sleep")
        self.mock_sleep.start()

        # Initialize with empty args
        set_module_args({})

        self.addCleanup(self.mock_module.stop)
        self.addCleanup(self.mock_sleep.stop)

    def execute_module(self, changed=None, commands=None, failed=False):
        """
        Helper method to execute a module and verify results.
        
        Args:
            changed: Expected value of changed flag (or None to skip check)
            commands: Expected commands (or None to skip check)
            failed: Whether module execution is expected to fail
            
        Returns:
            dict: The result dict from module execution
        """
        try:
            # Module code should raise one of these exceptions
            pass
        except AnsibleExitJson as exc:
            result = exc.args[0] if exc.args else {}
            
            if failed:
                self.fail(f"Module exit unexpectedly succeeded: {result}")
            
            if changed is not None:
                self.assertEqual(
                    result.get("changed"),
                    changed,
                    f"Expected changed={changed}, got {result.get('changed')}"
                )
            
            if commands is not None:
                self.assertEqual(
                    result.get("commands"),
                    commands,
                    f"Commands mismatch. Expected: {commands}, Got: {result.get('commands')}"
                )
            
            return result
            
        except AnsibleFailJson as exc:
            result = exc.args[0] if exc.args else {}
            
            if not failed:
                self.fail(f"Module failed unexpectedly: {result}")
            
            return result
