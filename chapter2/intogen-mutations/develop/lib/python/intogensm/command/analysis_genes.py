from intogensm.command import RunCommand
from intogensm.analysis import DRIVERS_FLOW_NAME

class DriversCommand(RunCommand):

	cmd_name = "drivers"

	def execute(self):

		self._wok_run(DRIVERS_FLOW_NAME)
