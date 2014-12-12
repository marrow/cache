# encoding: utf-8

import os
import sys


class Mine(object):
	def canary(self):
		pass

if not hasattr(Mine.canary, 'im_class') and not hasattr(Mine.canary, '__qualname__'):
	os.environ['CANARY'] = "DEAD"


def pytest_cmdline_preparse(args):
	args[:] = ['--cov-config', '.coveragerc-' + str(sys.version_info[0])] + args
