import utils
import sys
from pyVmomi import vim, vmodl

def wait_for_task(task):
    """ 
    Wait for a vCenter task to finish. 
    This function continuously checks the state of the task 
    until it is either successful or encounters an error.
    """
    task_done = False
    while not task_done:
        if task.info.state == 'success':
            return task.info.result  # Return the result if the task was successful

        if task.info.state == 'error':
            print("there was an error")  # Print error message if task failed
            print(task.info.error)
            task_done = True

# Add an SCSI controller to a virtual machine (VM)
def add_scsi_controller(vm):
    """
    This function adds a ParaVirtual SCSI controller to the specified VM.
    """
    devices = []
    spec = vim.vm.ConfigSpec()
     
    scsi_ctr = vim.vm.device.VirtualDeviceSpec()
    scsi_ctr.operation = vim.vm.device.VirtualDeviceSpec.Operation.add  # Set operation to add
    scsi_ctr.device = vim.vm.device.ParaVirtualSCSIController()  # Create a new SCSI controller
    scsi_ctr.device.busNumber = 1  # Specify the bus number for the SCSI controller
    scsi_ctr.device.hotAddRemove = True  # Allow hot add/remove of devices
    scsi_ctr.device.sharedBus = 'noSharing'  # Configure shared bus settings
    scsi_ctr.device.scsiCtlrUnitNumber = 7  # Set the unit number for the SCSI controller
    devices.append(scsi_ctr)  
    
    spec.deviceChange = devices  # Assign the device changes to the spec
    wait_for_task(vm.ReconfigVM_Task(spec=spec))  # Reconfigure the VM to apply changes
    print(f"SCSI controller added to {vm.name}.")  # Confirmation message

def add_disk(vm, data):
    """
    Add a disk to the specified VM.
    This function determines the next available unit number, 
    creates a new virtual disk, and adds it to the VM's configuration.
    """
    spec = vim.vm.ConfigSpec()
    unit_number = 0
    controller = None

    # Iterate through existing devices to find the next available unit number
    for device in vm.config.hardware.device:
        if hasattr(device.backing, 'fileName'):
            unit_number = int(device.unitNumber) + 1  # Increment unit number for next disk
            if unit_number == 7:  # Skip reserved unit number for SCSI controller
                unit_number += 1
            if unit_number >= 16:  # Limit the number of disks
                print("we don't support this many disks")
                return -1
        if isinstance(device, vim.vm.device.VirtualSCSIController):
            controller = device  # Store the SCSI controller reference

    if controller is None:
        print("Disk SCSI controller not found!")
        return -1  # Exit if no SCSI controller found

    # Prepare to add the new disk
    dev_changes = []
    new_disk_kb = int(data["disk_size"]) * 1024  # Convert disk size from MB to KB
    disk_spec = vim.vm.device.VirtualDeviceSpec()
    disk_spec.fileOperation = "create"  # Set operation to create a new disk
    disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add  # Specify add operation
    disk_spec.device = vim.vm.device.VirtualDisk()  # Create a new virtual disk
    disk_spec.device.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()  # Disk backing info
    
    if data["disk_type"] == 'thin':
        disk_spec.device.backing.thinProvisioned = True  # Enable thin provisioning if specified

    disk_spec.device.backing.diskMode = 'persistent'  # Set disk mode
    disk_spec.device.unitNumber = unit_number  # Assign the next available unit number
    disk_spec.device.capacityInKB = new_disk_kb  # Set disk capacity
    disk_spec.device.controllerKey = controller.key  # Link to the SCSI controller
    dev_changes.append(disk_spec)  # Add disk specification to changes
    spec.deviceChange = dev_changes  # Assign device changes to spec
    wait_for_task(vm.ReconfigVM_Task(spec=spec))  # Reconfigure the VM to apply changes
    print("%sMB disk added to %s" % (data["disk_size"], vm.config.name))  # Confirmation message
    return 0

def create_dummy_vm(data, vm_folder, resource_pool, datastore, si):
    """ 
    Creates a dummy Virtual Machine (VM) with specified resources.
    
    :param data: Configuration data for the VM
    :param vm_folder: Folder to place the VM in
    :param resource_pool: Resource Pool for VM allocation
    :param datastore: Datastore for VM storage
    :param si: ServiceInstance connection
    """
    datastore_path = '[' + datastore.name + ']'

    # Basic VM configuration with no disks
    vmx_file = vim.vm.FileInfo(logDirectory=None,
                               snapshotDirectory=None,
                               suspendDirectory=None,
                               vmPathName=datastore_path)
    
    config = vim.vm.ConfigSpec(name=data["vm_name"], memoryMB=data["ram"], numCPUs=data["cpu"],
                               files=vmx_file, guestId='dosGuest', version='vmx-07')
    
    print("Creating VM {}...".format(data["vm_name"]))
    task = vm_folder.CreateVM_Task(config=config, pool=resource_pool)  # Create VM task
    wait_for_task(task)  # Wait for the VM creation to finish
    
    vm = utils.get_vm(si.content, data["vm_name"])  # Retrieve the newly created VM
    add_scsi_controller(vm)  # Add an SCSI controller to the VM
    add_disk(vm, data)  # Add a disk to the VM

def find_free_ide_controller(vm):
    """ 
    Find a free IDE controller in the VM to attach devices.
    
    :param vm: Virtual Machine object
    :return: Free IDE controller or None if not found
    """
    for dev in vm.config.hardware.device:
        if isinstance(dev, vim.vm.device.VirtualIDEController):
            # If there are less than 2 devices attached, we can use it.
            if len(dev.device) < 2:
                return dev
    return None  # Return None if no free IDE controller is found

def new_cdrom_spec(controller_key, backing):
    """ 
    Create a new CD-ROM specification for the VM.
    
    :param controller_key: The key of the IDE controller
    :param backing: The backing information for the CD-ROM
    :return: VirtualCdrom object
    """
    connectable = vim.vm.device.VirtualDevice.ConnectInfo()
    connectable.allowGuestControl = True  # Allow guest OS to control the CD-ROM
    connectable.startConnected = True  # Start connected to the VM

    cdrom = vim.vm.device.VirtualCdrom()
    cdrom.controllerKey = controller_key  # Set controller key
    cdrom.key = -1  # Assign a key (default -1 for new devices)
    cdrom.connectable = connectable  # Set connectable properties
    cdrom.backing = backing  # Assign backing info
    return cdrom  # Return the CD-ROM object

def find_device(vm, device_type):
    """ 
    Find devices of a specific type in the VM.
    
    :param vm: Virtual Machine object
    :param device_type: The type of device to find
    :return: List of devices found
    """
    result = []
    for dev in vm.config.hardware.device:
        if isinstance(dev, device_type):
            result.append(dev)  # Add device to result list if it matches the type
    return result

def cdrom_vm(data, si, datacenter):
    """ 
    Configure a CD-ROM for the specified VM, either adding or editing an ISO.
    
    :param data: Configuration data
    :param si: ServiceInstance connection
    :param datacenter: Datacenter object
    """
    vm = si.content.searchIndex.FindChild(datacenter.vmFolder, data["vm_name"])
    if vm is None:
        raise Exception('Failed to find VM %s in datacenter %s' % (data["vm_name"], datacenter.name))  # Raise an exception if VM not found

    controller = find_free_ide_controller(vm)  # Find a free IDE controller
    if controller is None:
        raise Exception('Failed to find a free slot on the IDE controller')  # Raise exception if no free slot found

    cdrom = None  # Initialize CD-ROM variable
    
    cdrom_operation = vim.vm.device.VirtualDeviceSpec.Operation
    iso = data["cdrom"]
    if iso is not None:
        device_spec = vim.vm.device.VirtualDeviceSpec()
        if cdrom is None:  # Add a new CD-ROM if not found
            backing = vim.vm.device.VirtualCdrom.IsoBackingInfo(fileName=iso)  # Specify ISO backing
            cdrom = new_cdrom_spec(controller.key, backing)  # Create a new CD-ROM specification
            device_spec.operation = cdrom_operation.add  # Set operation to add
        else:  # Edit an existing CD-ROM
            backing = vim.vm.device.VirtualCdrom.IsoBackingInfo(fileName=iso)  # Specify ISO backing
            cdrom.backing = backing  # Update the backing info
            device_spec.operation = cdrom_operation.edit  # Set operation to edit
        device_spec.device = cdrom  # Assign the CD-ROM to the device specification
        config_spec = vim.vm.ConfigSpec(deviceChange=[device_spec])  # Create config specification
        wait_for_task(vm.Reconfigure(config_spec))  # Reconfigure the VM with the new CD-ROM

        cdroms = find_device(vm, vim.vm.device.VirtualCdrom)  # Find existing CD-ROMs

        # Verify if the CD-ROM added is the same as the one specified
        cdrom = None
        for x in cdroms:
            if isinstance(x.backing, type(backing)) and x.backing.fileName == iso:
                cdrom = x
                break
        
    else:
        print('Skipping ISO test as no iso provided.')  # Skip if no ISO path is given

    if cdrom is not None:  # If a CD-ROM was found, remove it
        device_spec = vim.vm.device.VirtualDeviceSpec()
        device_spec.device = cdrom  # Assign the CD-ROM to the device specification
        device_spec.operation = cdrom_operation.remove  # Set operation to remove
        config_spec = vim.vm.ConfigSpec(deviceChange=[device_spec])  # Create config specification
        wait_for_task(vm.Reconfigure(config_spec))  # Reconfigure the VM to remove the CD-ROM

def main():
    """ 
    Main entry point of the script. 
    This function connects to vCenter, reads VM configuration data, 
    and creates and configures a dummy VM and its CD-ROM.
    """
    si = utils.connect()  # Connect to vCenter
    data = utils.read_json("./json/vm_conf.json")  # Read VM configuration from JSON file
    vm_folder = si.content.rootFolder.childEntity[0].vmFolder  # Get the VM folder
    resource_pool = si.content.rootFolder.childEntity[0].hostFolder.childEntity[0].resourcePool  # Get the resource pool
    datastore = si.content.rootFolder.childEntity[0].datastore[0]  # Get the datastore
    datacenter = si.content.rootFolder.childEntity[0]  # Get the datacenter
    
    create_dummy_vm(data, vm_folder, resource_pool, datastore, si)  # Create the dummy VM
    cdrom_vm(data, si, datacenter)  # Configure the CD-ROM for the VM
    
    vm = utils.get_vm(si.content, data["vm_name"])  # Retrieve the newly created VM
    power_on = vm.PowerOnVM_Task()  # Power on the VM
    wait_for_task(power_on)  # Wait for the power on task to complete
    
    print("VM launched.")  # Confirmation message once VM is launched

if __name__ == "__main__":
    main()  # Execute the main function when the script is run