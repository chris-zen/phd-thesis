from intogensm.command import RunCommand
from intogensm.analysis import RESULTS_FLOW_NAME

class ResultsCommand(RunCommand):

	cmd_name = "results"

	def execute(self):

		self._wok_run(RESULTS_FLOW_NAME)
