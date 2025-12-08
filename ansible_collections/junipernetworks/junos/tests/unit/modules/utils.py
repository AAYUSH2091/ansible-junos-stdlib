from __future__ import absolute_import, division, print_function

__metaclass__ = type
import json

from unittest import TestCase
from unittest.mock import patch

try:
    from ansible.module_utils.testing import patch_module_args
except ImportError:
    from contextlib import contextmanager
    from ansible.module_utils import basic
    from ansible.module_utils._text import to_bytes

    @contextmanager
    def patch_module_args(args=None):
        """Fallback implementation for older Ansible versions"""
        if args is None:
            args = {}
        
        if "_ansible_remote_tmp" not in args:
            args["_ansible_remote_tmp"] = "/tmp"
        if "_ansible_keep_remote_files" not in args:
            args["_ansible_keep_remote_files"] = False
        
        args_json = json.dumps({"ANSIBLE_MODULE_ARGS": args})
        basic._ANSIBLE_ARGS = to_bytes(args_json)
        
        try:
            yield
        finally:
            basic._ANSIBLE_ARGS = None


class AnsibleExitJson(Exception):
    pass


class AnsibleFailJson(Exception):
    pass


def exit_json(*args, **kwargs):
    if "changed" not in kwargs:
        kwargs["changed"] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    kwargs["failed"] = True
    raise AnsibleFailJson(kwargs)


class ModuleTestCase(TestCase):
    """Base test case class for Ansible modules"""
    
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
        
        self.addCleanup(self.mock_module.stop)
        self.addCleanup(self.mock_sleep.stop)
    
    def execute_module(self, module_args=None, check_mode=False, changed=False, 
                      commands=None, failed=False):
        """
        Execute module with given arguments using official patch_module_args
        
        Args:
            module_args: Dict of module arguments
            check_mode: Enable check mode
            changed: Expected changed status
            commands: Expected commands
            failed: Expected failed status
        """
        if module_args is None:
            module_args = {}
        
        if check_mode:
            module_args["_ansible_check_mode"] = True
        
        # Use the official context manager to patch module args
        with patch_module_args(module_args):
            try:
                # This will call your module's main()
                # which should raise AnsibleExitJson or AnsibleFailJson
                pass
            except AnsibleExitJson as exc:
                result = exc.args[0]
                if failed:
                    self.fail(f"Module failed unexpectedly: {result}")
                if changed is not None:
                    self.assertEqual(result.get("changed"), changed)
                return result
            except AnsibleFailJson as exc:
                result = exc.args[0]
                if not failed:
                    self.fail(f"Module failed: {result}")
                return result
