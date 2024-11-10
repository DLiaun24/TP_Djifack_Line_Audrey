import utils
import sys

from pyVmomi import vim, vmodl

def wait_for_task(task):
    """ wait for a vCenter task to finish """
    task_done = False
    while not task_done:
        if task.info.state == 'success':
            return task.info.result

        if task.info.state == 'error':
            print("there was an error")
            print(task.info.error)
            task_done = True

def create_dummy_vm(data, vm_folder, resource_pool, datastore):
    """Creates a dummy VirtualMachine with 1 vCpu, 128MB of RAM.

    :param name: String Name for the VirtualMachine
    :param si: ServiceInstance connection
    :param vm_folder: Folder to place the VirtualMachine in
    :param resource_pool: ResourcePool to place the VirtualMachine in
    :param datastore: DataStrore to place the VirtualMachine on
    """
    datastore_path = '[' + datastore.name + ']'

    # bare minimum VM shell, no disks. Feel free to edit
    vmx_file = vim.vm.FileInfo(logDirectory=None,
                               snapshotDirectory=None,
                               suspendDirectory=None,
                               vmPathName=datastore_path)


    # Define the VM configuration specifications
    config = vim.vm.ConfigSpec(name=data["vm_name"], memoryMB=data["ram"], numCPUs=data["cpu"],
                               files=vmx_file, guestId='dosGuest',
                               version='vmx-07')

    # Log the VM creation process
    print("Creating VM {}...".format(data["vm_name"]))
    
    # Create the VM task
    task = vm_folder.CreateVM_Task(config=config, pool=resource_pool)
    wait_for_task(task)
    
def find_free_ide_controller(vm):
    """ 
    Finds a free IDE controller in the specified VM.

    :param vm: The Virtual Machine to search for an IDE controller
    :return: The first free IDE controller or None if none is found
    """

    for dev in vm.config.hardware.device:
        # Check if it's an IDE controller
            # If less than 2 devices are attached, we can use this controller
        
        if isinstance(dev, vim.vm.device.VirtualIDEController):
            # If there are less than 2 devices attached, we can use it.
            if len(dev.device) < 2: # Return the available IDE controller
                return dev 
    return None

def new_cdrom_spec(controller_key, backing):
    """ 
    Creates a new CD-ROM device specification.

    :param controller_key: The key of the IDE controller to attach the CD-ROM to
    :param backing: The backing information for the CD-ROM
    :return: A new CD-ROM device specification
    """

    # Create connectable info for the CD-ROM
    connectable = vim.vm.device.VirtualDevice.ConnectInfo()
    connectable.allowGuestControl = True
    connectable.startConnected = True

    # Create a new CD-ROM device
    cdrom = vim.vm.device.VirtualCdrom()

    # Set the controller key
    cdrom.controllerKey = controller_key
    
     # Set the device key to -1 (to be assigned by vCenter)
    cdrom.key = -1

    # Set the connectable info
    cdrom.connectable = connectable
    # Set the backing information
    cdrom.backing = backing

    # Return the new CD-ROM device specification
    return cdrom

def find_device(vm, device_type):
    """ 
    Finds all devices of a specific type in the given VM.

    :param vm: The Virtual Machine to search
    :param device_type: The type of device to find (e.g., CD-ROM)
    :return: A list of devices of the specified type
    """

    result = []  # Initialize a list to store found devices
    for dev in vm.config.hardware.device:
         # Check if the device matches the specified type
        if isinstance(dev, device_type):
            result.append(dev)
    return result


def cdrom_vm(data, si, datacenter):
    """ 
    Configures the CD-ROM for a specified Virtual Machine.

    :param data: Configuration data containing the VM name and CD-ROM path
    :param si: ServiceInstance connection to vCenter
    :param datacenter: Datacenter where the VM resides
    """

    # Find the specified VM by name in the datacenter
    vm = si.content.searchIndex.FindChild(datacenter.vmFolder, data["vm_name"])
    if vm is None:
        raise Exception('Failed to find VM %s in datacenter %s' %
                        (data["vm_name"], datacenter.name))
        # Raise an error if the VM is not found

    # Find a free IDE controller for the VM
    controller = find_free_ide_controller(vm)
    if controller is None:
        raise Exception('Failed to find a free slot on the IDE controller')
        # Raise an error if no free controller is found
    
    cdrom = None # Initialize the CD-ROM variable
    
    # Get the device operation enum
    cdrom_operation = vim.vm.device.VirtualDeviceSpec.Operation
    
    # Get the ISO file path from the configuration data
    iso = data["cdrom"]
    
    if iso is not None:# If an ISO file is provided
        device_spec = vim.vm.device.VirtualDeviceSpec()
        if cdrom is None:  # If no CD-ROM has been added yet
            backing = vim.vm.device.VirtualCdrom.IsoBackingInfo(fileName=iso)
            cdrom = new_cdrom_spec(controller.key, backing)
            device_spec.operation = cdrom_operation.add
        else:  # edit an existing cdrom
            backing = vim.vm.device.VirtualCdrom.IsoBackingInfo(fileName=iso)
            cdrom.backing = backing
            device_spec.operation = cdrom_operation.edit
        device_spec.device = cdrom
        config_spec = vim.vm.ConfigSpec(deviceChange=[device_spec])
        wait_for_task(vm.Reconfigure(config_spec))

        cdroms = find_device(vm, vim.vm.device.VirtualCdrom)

        # TODO isinstance(x.backing, type(backing))
        cdrom = None
        for x in cdroms:
            if isinstance(x.backing, type(backing)) and x.backing.fileName == iso:
                cdrom = x
                break
                     
        
    else:
        print('Skipping ISO test as no iso provided.')

    if cdrom is not None:  # If a CD-ROM was found, remove it
        # Create a new device specification
        device_spec = vim.vm.device.VirtualDeviceSpec()
        # Assign the CD-ROM device
        device_spec.device = cdrom
        # Set operation to remove the CD-ROM
        device_spec.operation = cdrom_operation.remove
        # Create configuration specification for the change
        config_spec = vim.vm.ConfigSpec(deviceChange=[device_spec])
        # Apply the reconfiguration
        wait_for_task(vm.Reconfigure(config_spec))


def main():
    """Main function to execute the script."""
    si = utils.connect()
    data = utils.read_json("./json/vm_conf.json")

    vm_folder = si.content.rootFolder.childEntity[0].vmFolder
    resource_pool = si.content.rootFolder.childEntity[0].hostFolder.childEntity[0].resourcePool
    datastore = si.content.rootFolder.childEntity[0].datastore[0]
    datacenter = si.content.rootFolder.childEntity[0]
    
    create_dummy_vm(data, vm_folder, resource_pool, datastore)
    cdrom_vm(data, si, datacenter)
    
    vm = utils.get_vm(si.content, data["vm_name"])
    power_on = vm.PowerOnVM_Task()
    wait_for_task(power_on)
    
    print("VM launched.") # Log that the VM has been successfully launched

    
if __name__ == "__main__":
    sys.exit(main())