import paramiko
import json
from pyVim.connect import SmartConnect
from pyVmomi import vim
import re



#Function reads a JSON file and return its content as apython object (typically a dictionary or list)

def read_json(path):
    with open(path, "r") as file:
        return json.load(file)
#Load configuration from JSON file    
conf = read_json("./json/conf.json")


#Function to extract the file name from a given path
def get_file_name(path):
    pattern = r"[^\\/]+$" #Regular expression to match the file name
    match = re.search(pattern, path)   
    name = match.group(0) # Get the matched file name
    return name[:-4] #Return the name without the last four carachers (extension)



#Function to check and start the SSH service on the ESXi host
def check_ssh_service(content):
    # Access the first host in the ESXi cluster
    host_system = content.rootFolder.childEntity[0].hostFolder.childEntity[0].host[0]
    service_system = host_system.configManager.serviceSystem
    
    #Find the SSH service
    ssh_service = [x for x in service_system.serviceInfo.service if x.key == 'TSM-SSH'][0]
    
    #Start the SSH service if it's not running
    if not ssh_service.running:
        service_system.Start(ssh_service.key)
        print("SSH launched on the server.")
    else:
        print("SSH already running")


#Function to stop the SSH service on the EXSi host        

def stop_ssh_service(content):
    #Access the first host in the ESXi cluster
    host_system = content.rootFolder.childEntity[0].hostFolder.childEntity[0].host[0]
    service_system = host_system.configManager.serviceSystem
    
    # Find the SSH service
    ssh_service = [x for x in service_system.serviceInfo.service if x.key == 'TSM-SSH'][0]
    
    #STop the SSH service if it's running
    if ssh_service.running:
        service_system.Stop(ssh_service.key)
        print("SSH stopped on the server.")

#Function to execute a command via SSH on a remote server
def cmd_ssh(cmd):
    client = paramiko.SSHClient() # Create an SSH client
    client.load_system_host_keys() # Load system host keys

    #AUtomatically add unknoxn host Keys
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy)

    #Connect to the remote server using credentials from the config
    client.connect(conf["host"], conf["port"], conf["username"], conf["password"])
    #Execute the given command
    stdin, stdout, stderr = client.exec_command(cmd)
    
    output = stdout.read().decode() #Read standard output
    error = stderr.read().decode() #REad standard error

    #Print error output if available
    if(output):
        print("Command...")
        print(output)
    if(error):
        print("Error...")
        print(error)
    client.close() #Cclose the SSH connection


#Function to connect to the ESXi or vCenter server
def connect():
    """
    Connecion to ESXi/vCenter. 
     - host: the IP or hostname of the ESXi/vCenter
     - user: ESXi/vCenter user
     - pwd: ESXi/vCenter password
    """
    #Establish a connection to the ESXi/vCenter server
    service_instance = SmartConnect(host=conf["host"], user=conf["username"], pwd=conf["password"], disableSslCertValidation=True)
    #Return the service instance for further interactions
    return service_instance

def get_vm(content, vm_name = None):
    """
    Get the VM from its name
     - content: the vmWare ServiceContent
     - vm_name (optional): the name of the VM to retrieve
    """
    if vm_name is None:
        vm_name = "ouups" #Default name if none is provided
    container = content.rootFolder #Get the root folder of the VM
    view_type = [vim.VirtualMachine] #Specify the view type for VMs
    recursive = True # ENable recursion to find VMs in subfolders

    #Create a container view for VMs in the root folder
    container_view = content.viewManager.CreateContainerView(
        container, view_type, recursive
    )
    vm_list = container_view.view # Get the list of VMs in the view
    for vm in vm_list:
        if vm.name == vm_name:
            return vm #Return the VM object if found