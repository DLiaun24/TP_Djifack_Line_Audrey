import utils
from deploy_vm import deploy # Importation de la fonction de déploiement de machines virtuelles
import sys

from pyVmomi import vmodl

def wait_for_task(task):
    """ 
    Wait for a vCenter task to finish. 
    Returns the result if the task is successful, otherwise prints the error.
    """
    task_done = False
    while not task_done:
        if task.info.state == 'success':
            return task.info.result

        if task.info.state == 'error':
            print("there was an error")
            print(task.info.error)
            task_done = True

def main():
    si = utils.connect()

    data = utils.read_json('./json/ova.json')
    src = utils.get_file_name(data["ova_path"])
    
     # Access various vSphere resources
    file_manager = si.content.fileManager
    datacenter = si.content.rootFolder.childEntity[0]
    datastore = datacenter.datastore[0]
    resource_pool = si.content.rootFolder.childEntity[0].hostFolder.childEntity[0].resourcePool
    ovf_manager = si.content.ovfManager
    virtual_disk_manager = si.content.virtualDiskManager

    # Deploy the OVA file as the first instance
    deploy(data["ova_path"], 0, ovf_manager, resource_pool, datastore, datacenter)
    
    # Retrieve the deployed VM object
    vm = utils.get_vm(si.content, src)
    
     # Loop to create additional clones of the VM
    for i in range(data["num_instances"]-1):
        if i == 0:
            dest = f"{ src}_clone" # Name for the first clone
        else:
            dest = f"{ src}_clone{i}"  #Name for subsequent clones

        datastore_path = datastore.info.url
        # resource_pool = si.content.rootFolder.childEntity[0].hostFolder.childEntity[0].resourcePool
        path_from = f"[{datastore.name}]/{src}/{src}.vmdk"
        path_to = f"[{datastore.name}]/{dest}/{dest}.vmdk"
        
        # Power off the VM if it's currently powered on
        if(vm.runtime.powerState == "poweredOn"):
            power_off = vm.PowerOffVM_Task()
            wait_for_task(power_off)  # Wait for the power-off task to complete 
                
        try:
            # Create a directory for the clone in the datastore
            file_manager.MakeDirectory(f"[{datastore.name}]/{dest}", datacenter)
        except vmodl.MethodFault as ex:
            #Handle errors while creating the directory
            print("Hit an error while creating the directory: %s" % ex)
            return 1

         # Copy the virtual disk from the source to the destination        
        copy = virtual_disk_manager.CopyVirtualDisk_Task(sourceName = path_from, destName = path_to)
        wait_for_task(copy)

        # Check if the SSH service is running on the target VM    
        utils.check_ssh_service(si.content)
        
        # Copy and modify the VMX file for the cloned VM
        utils.cmd_ssh(f"cp {datastore_path}/{src}/{src}.vmx {datastore_path}/{dest}/{dest}.vmx")
        
        # Update the VMX file to replace the source name with the destination name
        utils.cmd_ssh(f"sed -i 's/{src}/{dest}/g' {datastore_path}/{dest}/{dest}.vmx")
        
        # Register the cloned VM with vCenter
        utils.cmd_ssh(f"vim-cmd solo/registervm {datastore_path}/{dest}/{dest}.vmx")
                
        
    return 0 # Return 0 indicating success
    
if __name__ == "__main__":
    sys.exit(main())