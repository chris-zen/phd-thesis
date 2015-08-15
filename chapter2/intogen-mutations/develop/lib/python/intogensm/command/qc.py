from intogensm.command import RunCommand
from intogensm.analysis import QC_FLOW_NAME

class QcCommand(RunCommand):

	cmd_name = "qc"

	def execute(self):

		self._wok_run(QC_FLOW_NAME)