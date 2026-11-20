import os

try:
    from do_utilities.Constants import github_file_path
except:
    from Constants import github_file_path


# Generates a requirements.txt file based on imported libraries
def generateRequirementsFile(repo_name):
    try:
        
        repo_path = os.path.join(github_file_path, repo_name)
        requirements_path = os.path.join(repo_path, "requirements.txt")
        
        command = f"python.exe -m pip list --format=freeze > {requirements_path}"
        
        os.chdir(repo_path)
        data_ops_libraries = getDataOpsDependencies(repo_name)
        os.system(command)
        
        with open(requirements_path, "r", encoding = "utf-8") as file:
            requirements = [
                line
                for line in file
                if line.strip() and "#" != line.strip()[0] and len(line.strip()) > 1
            ]
        with open(requirements_path, "w", encoding = "utf-8") as file:
            for cur_library in requirements:
                if cur_library.split("=")[0] in data_ops_libraries:
                    cur_library = cur_library.split("=")[0]
                    cur_library = f"{cur_library.replace("-", "_")} @ git+https://github.com/4mativ/{cur_library}.git@main\n"
                cur_library = cur_library.replace("==", "~=")
                file.write(cur_library)
    except Exception:
        print("Failed to generate new reqiurements file")


def forceReinstallLibrary(repo_name, library):
    try:
        command = f"python.exe -m pip install --upgrade --force-reinstall --no-deps "
        if library[:3] in ["do_", "do-"]:
            library = library.replace("_", "-")
            command += f"git+https://github.com/4mativ/{library}.git@main"
        else:
            command += library
        
        repo_path = os.path.join(github_file_path, repo_name)
        os.chdir(repo_path)
        print(command)
        os.system(command)
    except Exception as ex:
        print(ex, "Failed to force re-install", library)


def getDataOpsDependencies(repo_name):
    
    try:
        requirements_path = os.path.join(github_file_path, repo_name, "requirements.txt")
        if not os.path.isfile(requirements_path):
            return []
        
        with open(requirements_path, "r", encoding = "utf-8") as file:
            requirements = [
                line.strip().split(" ")[0]
                for line in file
                if line.strip() and "@" in line.strip()
            ]
        return requirements
    except Exception as ex:
        print(ex, "Failed to find data ops dependencies in existing requirements file")
        return []


def forceReinstallDataOpsLibraries(repo_name):
    
    requirements = getDataOpsDependencies(repo_name)
    
    for cur_library in requirements:
        forceReinstallLibrary(repo_name, cur_library)


if __name__ == "__main__":
    repo = "do-utilities"
    generateRequirementsFile(repo)
    forceReinstallDataOpsLibraries(repo)
