import re
import subprocess


class CheckTag():
            
    def check_tag(self):
        setuppy_version = self.get_tag_in_setuppy("setup.py")
        tag_version = self.get_latest_tag()
        print("The version number in setup.py is : ", setuppy_version)
        print("The version number in git tag is : ", tag_version)
        return setuppy_version == tag_version
    
    def get_latest_tag(self):
        proc = subprocess.Popen(["git", "describe", "--tag"], 
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        version = stdout.strip().decode('utf-8')
        pattern = r"v(\d+).(\d+).(\d+)(.*?)"
        match = re.match(pattern, version)
        if(match):
            major = match.group(1)
            minor = match.group(2)
            build = match.group(3)
            return "v"+".".join((major, minor, build))
        else:
            return ""
            
    def get_tag_in_setuppy(self, file_path):
        pattern = r"version='(\d+).(\d+).(\d+)',"
        with open(file_path) as fo:
            for line in fo:
                if line.strip().startswith("version"):
                    match = re.match(pattern, line.strip())
                    if(match):
                        major = match.group(1)
                        minor = match.group(2)
                        build = match.group(3)
                        return "v"+".".join((major, minor, build))
        return ""
                
if __name__ == '__main__':
    ct = CheckTag()
    if not ct.check_tag():
        raise Exception("The version number in setup.py and git tag do not match")
        
        
    
    