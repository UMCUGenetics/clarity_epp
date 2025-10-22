from genologics.entities import Process
from genologics.lims import Lims
import config

class LimsInterface:
    def __init__(self, baseuri, username, password):
        self.lims = Lims(config.baseuri, config.username, config.password)

    def get_samples(self, project_id):
        return self.lims.get_samples(projectlimsid=project_id)

    def get_process(self, process_id):
        return Process(self.lims, id=process_id)

    def get_file_contents(self, file_id):
        return self.lims.get_file_contents(file_id).data.decode('utf-8')

# Singleton instantie
_lims_interface_instance = None

def get_lims_interface():
    global _lims_interface_instance
    if _lims_interface_instance is None:
        _lims_interface_instance = LimsInterface(config.baseuri, config.username, config.password)
    return _lims_interface_instance