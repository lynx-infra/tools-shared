import os
from merge_request import MergeRequest
import subprocess
import sys

class Config:
    def __init__(self):
        mr = MergeRequest()
        root_dir = mr.GetRootDirectory()
        config_path = os.path.join(root_dir, ".lcm_tools_config.yml")
        self.config = {}
        if os.path.exists(config_path):
            try:
                import yaml
            except ImportError:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "PyYAML~=6.0"])
                import yaml
            with open(config_path,encoding='utf-8') as config_f:
                config_json = yaml.load(config_f,Loader=yaml.FullLoader)
                self.config = config_json
        print("###config:",self.config)
    def get(self, key):
        return self.config.get(key)


config = Config()
