#!/usr/bin/env python
# -*- coding: utf-8; mode: python; py-indent-offset: 4; py-continuation-offset: 4 -*-
"""
"""
from __future__ import print_function
import sys


sys.dont_write_bytecode = True

import os


sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest import TestCase
try:                             # pragma: no cover
    import unittest.mock as mock # pragma: no cover
except:                          # pragma: no cover
    import mock                  # pragma: no cover
from mock import Mock
from mock import MagicMock
from mock import patch

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

from setenvironment import ModuleHelper

from .common import *

# ===========================
#   M O C K   H E L P E R S
# ===========================



class mock_run_status_error_rc1(object):
    """
    Mock for ``subprocess.run``. Has ``returncode=1``.
    """

    def __init__(self, cmd, stdout=None, stderr=None, shell=True):
        print(f"mock_run> {cmd}")
        self.stdout = b''
        self.stderr = b'Error for subprocess.run here'
        self.returncode = 1



class mock_popen_status_error_return_nonetype(mock_popen):
    """
    Specialization of popen mock that will return with error.
    """

    def __init__(self, cmd, stdout=None, stderr=None):
        super(mock_popen_status_error_return_nonetype, self).__init__(cmd, stdout, stderr)

    def communicate(self):
        print("mock_popen> communicate()")
        # Raise this via stdout within env_modules_python.module
        # to ensure that 'test_ModuleHeler_module_load_error_module_returns_nonetype'
        # passes on LMOD systems.
        stdout = b"raise TypeError('ERROR: the errorcode can not be `None`')"
        stderr = b""
        self.returncode = None
        return (stdout, stderr)



class mock_popen_status_error_rc1(mock_popen):
    """
    Specialization of popen mock that will return with error.

    Test the condition where modulecmd returned a status of 1 and
    has `ERROR:` in its stderr field.
    """

    def __init__(self, cmd, bufsize=None, shell=None, stdout=None, stderr=None):
        super(mock_popen_status_error_rc1, self).__init__(cmd, bufsize, shell, stdout, stderr)

    def communicate(self):
        print("mock_popen> communicate()")
        stdout = b"stdout=1"
        stderr = b"ERROR: Something wrong happened."
        self.returncode = 1
        return (stdout, stderr)



class mock_popen_status_error_rc0(mock_popen):
    """
    Specialization of popen mock.

    Simulates the results from a modulecmd operation that had
    an error loading a module (maybe not found). Modulecmd will tend
    to have a message like "ERROR: could not load module" in its stderr
    field but it will generally return an exit status of 0.
    """

    def __init__(self, cmd, bufsize=None, shell=None, stdout=None, stderr=None):
        super(mock_popen_status_error_rc0,
              self).__init__(cmd, bufsize=bufsize, shell=shell, stdout=stdout, stderr=stderr)
        sys.stderr.write("ERROR: Something wrong happened.")

    def communicate(self):
        print("mock_popen> communicate()")
        stdout = b"os.environ['__foobar__'] ='baz'\ndel os.environ['__foobar__']"
        stderr = b"ERROR: Something wrong happened."
        self.returncode = 0
        return (stdout, stderr)



class mock_popen_status_mlstatus_success(mock_popen):
    """
    Specialization of popen mock that will return with error (status==1)
    and stderr containing '_mlstatus = True' which happens on some systems.
    """

    def __init__(self, cmd, bufsize=None, shell=None, stdout=None, stderr=None):
        super(mock_popen_status_mlstatus_success, self).__init__(cmd, bufsize, shell, stdout, stderr)

    def communicate(self):
        print("mock_popen> communicate()")
        stdout = b"_mlstatus = True"
        stderr = b""
        self.returncode = 0
        return (stdout, stderr)



class mock_popen_status_mlstatus_error(mock_popen):
    """
    Specialization of popen mock that will return with error (status==1)
    and stderr containing '_mlstatus = False' which happens on some systems.
    """

    def __init__(self, cmd, bufsize=None, shell=None, stdout=None, stderr=None):
        super(mock_popen_status_mlstatus_error, self).__init__(cmd, bufsize, shell, stdout, stderr)

    def communicate(self):
        print("mock_popen> communicate()")
        stdout = b"_mlstatus = False"
        stderr = b""
        self.returncode = 0
        return (stdout, stderr)



class mock_popen_stdout_throws_on_exec(mock_popen):
    """
    This is a special mock function to replace the Popen instruction
    in ModuleHelper with one that returns a python command in its stdout
    which will raise an exception when it is run through `exec()`
    """

    def __init__(self, cmd, stdout=None, stderr=None):
        super(mock_popen_stdout_throws_on_exec, self).__init__(cmd, stdout, stderr)

    def communicate(self):
        print("mock_popen> communicate()")
        stdout = b"raise Exception('Exception generated by mock popen')"
        stderr = b""
        self.returncode = 0
        return (stdout, stderr)



def mock_distutils_spawn_find_executable_raise(*args, **kwargs):
    argstr = ",".join(args)
    print("[mock] `distutils.spawn.find_executable({})` -> Raise Exception".format(argstr))
    raise Exception("[mock] Exception goes boom!")



def mock_shutil_which_returns_none(*args, **kwargs):
    argstr = ",".join(args)
    print("[mock] `shutil.which({})` -> None".format(argstr))
    return None



original_system = os.system



def mock_system_status_error(cmd):
    """
    Override of system mock that will return with error (status==1)
    """
    print("mock_system> system(" + cmd + ")")
    # Run the original system command too but ignore the return code
    ret = original_system(cmd)
    return 1



def mock_system_status_ok(cmd):
    """
    Override of system mock that will return with success (status==0)
    """
    print("mock_system> system(" + cmd + ")")
    # Run the original system command too but ignore the return code
    ret = original_system(cmd)
    return 0



original_getenv = os.getenv



def mock_getenv_empty(cmd):
    """
    Override of getenv mock that will return the empty string ("")
    """
    print("mock_system> getenv(" + cmd + ")")
    # Run the original system command too but ignore the return code
    ret = original_getenv(cmd)
    return ""



# =======================================
#   M O D U L E H E L P E R   T E S T S
# =======================================



class ModuleHelperTest(TestCase):
    """
    Main test driver for the module() function provided by the
    ModuleHelper.py file
    """

    def setUp(self):
        ModuleHelper.module("use", "src/setenvironment/unittests/modulefiles")
        return

    @patch('subprocess.run', side_effect=mock_run_status_ok)
    @patch('subprocess.Popen', side_effect=mock_popen_status_ok)
    @patch('os.system', side_effect=mock_system_status_ok)
    def test_ModuleHelper_module_load_status_ok(self, arg_system, arg_popen, arg_run):
        r = ModuleHelper.module("load", "sems-gcc/4.8.4")
        print("result = {}".format(r))
        self.assertEqual(0, r)
        return

    @patch('subprocess.run', side_effect=mock_run_status_ok)
    def test_ModuleHelper_module_load_status_error_return(self, arg_run):
        with patch('subprocess.Popen', side_effect=mock_popen_status_error_rc1):
            with patch('os.system', side_effect=mock_system_status_error):
                r = ModuleHelper.module("load", "sems-gcc/4.8.4")
        print("result = {}".format(r))
        self.assertNotEqual(0, r)
        return

    @patch('subprocess.run', side_effect=mock_run_status_ok)
    def test_ModuleHelper_module_load_status_error_stderr(self, arg_run):
        try:
            with patch('env_modules_python.Popen', side_effect=mock_popen_status_error_rc0):
                r = ModuleHelper.module("load", "sems-gcc/4.8.4")
        except:
            with patch('subprocess.Popen', side_effect=mock_popen_status_error_rc0):
                r = ModuleHelper.module("load", "sems-gcc/4.8.4")
        print("result = {}".format(r))
        self.assertNotEqual(0, r)
        return

    @patch('subprocess.run', side_effect=mock_run_status_ok)
    @patch('subprocess.Popen', side_effect=mock_popen_status_ok)
    @patch('os.system', side_effect=mock_system_status_ok)
    def test_ModuleHelper_module_swap_status_ok(self, arg_system, arg_popen, arg_run):
        r = ModuleHelper.module("swap", "sems-gcc/4.8.4", "sems-gcc/7.3.0")
        print("result = {}".format(r))
        self.assertEqual(0, r)
        return

    @patch('subprocess.run', side_effect=mock_run_status_ok)
    #@patch('subprocess.Popen', side_effect=mock_popen_status_ok)
    def test_ModuleHelper_module_unload_status_ok(self, arg_run):
        with patch('subprocess.Popen', side_effect=mock_popen_status_ok):
            r = ModuleHelper.module("unload", "sems-gcc/4.8.4")
        print("result = {}".format(r))
        self.assertEqual(0, r)
        return

    @patch('subprocess.run', side_effect=mock_run_status_ok)
    def test_ModuleHelper_module_load_args_as_list(self, arg_run):
        """
        The `module()` function can take arguments in as a list.
        This tests that module works when the parameter is a list of arguments.
        """
        with patch('subprocess.Popen', side_effect=mock_popen_status_ok):
            r = ModuleHelper.module(["unload", "sems-gcc/4.8.4"])
        print("result = {}".format(r))
        self.assertEqual(0, r)
        return

    @patch('subprocess.run', side_effect=mock_run_status_ok)
    @patch('subprocess.Popen', side_effect=mock_popen_status_mlstatus_success)
    @patch('os.system', side_effect=mock_system_status_ok)
    def test_ModuleHelper_module_load_success_by_mlstatus(self, arg_system, arg_popen, arg_run):
        r = ModuleHelper.module("load", "sems-gcc/4.8.4")
        print("result = {}".format(r))
        self.assertEqual(0, r)
        return

    @patch('subprocess.run', side_effect=mock_run_status_ok)
    @patch('subprocess.Popen', side_effect=mock_popen_status_mlstatus_error)
    @patch('os.system', side_effect=mock_system_status_error)
    def test_ModuleHelper_module_load_error_by_mlstatus(self, arg_system, arg_popen, arg_run):
        r = ModuleHelper.module("load", "sems-gcc/4.8.4")
        print("result = {}".format(r))
        self.assertNotEqual(0, r)
        return

    @patch('subprocess.run', side_effect=mock_run_status_ok)
    @patch('distutils.spawn.find_executable', side_effect=Exception("mock side-effect error"))
    @patch('subprocess.Popen', side_effect=mock_popen_status_mlstatus_error)
    @patch('os.system', side_effect=mock_system_status_error)
    def test_ModuleHelper_module_load_error_no_modulecmd(
        self, arg_system, arg_popen, arg_find_executable, arg_run
    ):
        r = ModuleHelper.module("load", "sems-gcc/4.8.4")
        print("result = {}".format(r))
        self.assertNotEqual(0, r)
        return

    @patch('subprocess.run', side_effect=mock_run_status_ok)
    def test_ModuleHelper_module_load_error_exception(self, arg_run):
        """
        This tests the execution path in ModuleHelper in which the exec() command would
        throw an exception.
        In the Module call, we execute `modulehelper` so that it generates a list of
        Python commands. If one of them throws an exception we catch it, print a log message,
        and re-raise a BaseException.
        """
        try:
            with patch('env_modules_python.Popen', side_effect=mock_popen_stdout_throws_on_exec):
                with self.assertRaises(BaseException):
                    ModuleHelper.module("load", "gcc/4.8.4")
        except:
            with patch('subprocess.Popen', side_effect=mock_popen_stdout_throws_on_exec):
                with self.assertRaises(BaseException):
                    ModuleHelper.module("load", "gcc/4.8.4")
        return

    @patch('subprocess.run', side_effect=mock_run_status_ok)
    def test_ModuleHeler_module_load_error_module_returns_nonetype(self, arg_run):
        """
        This tests a failure when the `module()` function returns a NoneType
        object (i.e., like what happens with LMOD)
        """
        try:
            with patch('env_modules_python.Popen', side_effect=mock_popen_status_error_return_nonetype):
                with self.assertRaises(TypeError):
                    ModuleHelper.module("load", "gcc/4.8.4")

        except:
            with patch('subprocess.Popen', side_effect=mock_popen_status_error_return_nonetype):
                with self.assertRaises(TypeError):
                    ModuleHelper.module("load", "gcc/4.8.4")
        return

    @patch('subprocess.run', side_effect=mock_run_status_error_rc1)
    @patch('subprocess.Popen', side_effect=mock_popen_status_ok)
    @patch('distutils.spawn.find_executable', side_effect=mock_distutils_spawn_find_executable_raise)
    @patch('shutil.which', side_effect=mock_shutil_which_returns_none)
    @patch('os.getenv', side_effect=mock_getenv_empty)
    def test_ModuleHelper_modulecmd_not_found(
        self, arg_getenv, arg_shutil, arg_distutils, arg_popen, arg_run
    ):
        """
        Test a failure to find a `modulecmd` binary with the environment
        modules subsystem.
        """
        #with patch('distutils.spawn.find_executable', side_effect=mock_distutils_spawn_find_executable_raise):
        #with patch('shutil.which', side_effect=mock_shutil_which_returns_none):
        with self.assertRaises(FileNotFoundError):
            ModuleHelper.module("load", "sems-gcc/4.8.4")

        return
