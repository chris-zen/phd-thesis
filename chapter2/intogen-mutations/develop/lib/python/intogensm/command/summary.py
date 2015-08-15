from intogensm.command import RunCommand
from intogensm.analysis import SUMMARY_FLOW_NAME

class SummaryCommand(RunCommand):

	cmd_name = "summary"

	def execute(self):

		self._wok_run(SUMMARY_FLOW_NAME)