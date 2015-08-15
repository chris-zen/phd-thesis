from intogensm.command import RunCommand
from intogensm.analysis import COMBINATION_FLOW_NAME

class CombinationCommand(RunCommand):

	cmd_name = "combination"

	def execute(self):

		self._wok_run(COMBINATION_FLOW_NAME)
