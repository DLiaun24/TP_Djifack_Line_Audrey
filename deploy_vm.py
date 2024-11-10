import utils #Importing utility functions for configuration and connection management
import os
import os.path
import sys
import ssl # Importing the SSL module for secure socket layer operations
import tarfile
import time

from threading import Timer
from six.moves.urllib.request import Request, urlopen # type: ignore

from pyVmomi import vim, vmodl

def deploy(path, index, ovf_manager, resource_pool, datastore, datacenter):
    
    """
    Deploy an OVA (Open Virtualization Archive) file to a VMware environment.
    Parameters:
        - path: Path to the OVA file
        - index: Instance index for naming
        - ovf_manager: OVF manager to handle the import
        - resource_pool: Resource pool for deploying the OVA
        - datastore: Datastore for storing the VM
        - datacenter: Datacenter where the VM will be deployed
    """

    ova =  OvfHandler(path) #Create an instance of OvfHandler to manage the OVA file
    ova_name = utils.get_file_name(path)
    cisp = vim.OvfManager.CreateImportSpecParams() #Create parameters for the import specification
        
    if(index == 0):# If this is the first instance
        # Create the import specification for the OVA
        cisr = ovf_manager.CreateImportSpec(ova.get_descriptor(), resource_pool, datastore, cisp)
            
    else:# For subsequent instances
        # Create the import specification for the OVA
        cisr = ovf_manager.CreateImportSpec(ova.get_descriptor().replace(f"<Name>{ova_name}</Name>", f"<Name>{ova_name}{index}</Name>"), resource_pool, datastore, cisp)


    ova.set_spec(cisr) # Set the import specification in the OVA handler
    lease = resource_pool.ImportVApp(cisr.importSpec, datacenter.vmFolder) # Start the import process
    while lease.state == vim.HttpNfcLease.State.initializing:
        print(f"Waiting for initialization : {index+1}...")
        time.sleep(1)
    
    if lease.state == vim.HttpNfcLease.State.error:  # Check if there was an error during initialization
        print("Error : ", lease.error)
        return 1
            
    if lease.state == vim.HttpNfcLease.State.done:
         # Inform the user of completion
        print(f"Uploaded OVA {index+1} terminated.")
        return 0

    # Inform the user of the ongoing deployment    
    print(f"Deployment of the OVA : {index+1}...")
    # Upload the disks associated with the OVA
    ova.upload_disks(lease, utils.conf["host"])
    print()


def main():

    """
    Main function to handle the deployment of multiple OVA instances.
    """ 
    # Connection to vCenter
    si = utils.connect()
    # Read configuration data from a JSON file
    data = utils.read_json("./json/ova.json")
    
    datacenter = si.content.rootFolder.childEntity[0]
    datastore = datacenter.datastore[0]
    resource_pool = si.content.rootFolder.childEntity[0].hostFolder.childEntity[0].resourcePool
    ovf_manager = si.content.ovfManager
    
    
    # Loop through the number of instances to deploy
    for i in range(data["num_instances"]):
        # Deploy each OVA instance
        deploy(data["ova_path"], i, ovf_manager, resource_pool, datastore, datacenter)
    
    return 0    
    

def get_tarfile_size(tarfile):
    """
    Determine the size of a file inside the tarball.
    If the object has a size attribute, use that. Otherwise seek to the end
    and report that.
    """
    if hasattr(tarfile, 'size'):
        return tarfile.size
    size = tarfile.seek(0, 2)
    tarfile.seek(0, 0)
    return size

class OvfHandler(object):
    """
    OvfHandler handles most of the OVA operations.
    It processes the tarfile, matches disk keys to files and
    uploads the disks, while keeping the progress up to date for the lease.
    """
    def __init__(self, ovafile):
        """
        Performs necessary initialization, opening the OVA file,
        processing the files and reading the embedded ovf file.
        """
        self.handle = self._create_file_handle(ovafile)# Create a file handle for the OVA file
        self.tarfile = tarfile.open(fileobj=self.handle)
        ovffilename = list(filter(lambda x: x.endswith(".ovf"),
                                  self.tarfile.getnames()))[0] # Find the OVF file in the tar
        
        ovffile = self.tarfile.extractfile(ovffilename)
        self.descriptor = ovffile.read().decode() # Read the contents of the OVF file as a string



    def _create_file_handle(self, entry):
        """
        A simple mechanism to pick whether the file is local or not.
        This is not very robust.
        """
        if os.path.exists(entry):# Check if the file exists locally
            return FileHandle(entry)
        return WebHandle(entry) 


    def get_descriptor(self):
        # Return the OVF descriptor string
        return self.descriptor

    def set_spec(self, spec):
        """
        The import spec is needed for later matching disks keys with
        file names.
        """
        self.spec = spec # Store the import specification for later use

    def get_disk(self, file_item):
        """
        Translation for disk key to file name, returning a file handle.
        """
        
        # Find the corresponding file name
        ovffilename = list(filter(lambda x: x == file_item.path,
                                  self.tarfile.getnames()))[0]
        # Extract and return the disk file
        return self.tarfile.extractfile(ovffilename)

    def get_device_url(self, file_item, lease):
        """
        Retrieve the device URL for a given file item from the lease.
        """
        
        # Iterate through device URLs in the lease
        for device_url in lease.info.deviceUrl:
            if device_url.importKey == file_item.deviceId:
                return device_url
        raise Exception("Failed to find deviceUrl for file %s" % file_item.path)

    def upload_disks(self, lease, host):
        """
        Uploads all the disks, with a progress keep-alive.
        """
        #Store the lease for progress tracking
        self.lease = lease
        try:
            self.start_timer()
            for fileItem in self.spec.fileItem:
                self.upload_disk(fileItem, lease, host)
            lease.Complete()
            print("Finished deploy successfully.")
            return 0
        except vmodl.MethodFault as ex:
            print("Hit an error in upload: %s" % ex)
            lease.Abort(ex)
        except Exception as ex:
            print("Lease: %s" % lease.info)
            print("Hit an error in upload: %s" % ex)
            lease.Abort(vmodl.fault.SystemError(reason=str(ex)))
        return 1

    def upload_disk(self, file_item, lease, host):
        """
        Upload an individual disk. Passes the file handle of the
        disk directly to the urlopen request.
        """
        # Get the disk file from the OVA
        ovffile = self.get_disk(file_item)

        # Check if the file was successfully retrieved
        if ovffile is None:
            return
        device_url = self.get_device_url(file_item, lease)
        url = device_url.url.replace('*', host)
        headers = {'Content-length': get_tarfile_size(ovffile)}
        
        # Check for SSL context creation capability
        if hasattr(ssl, '_create_unverified_context'):
            ssl_context = ssl._create_unverified_context()
        else:
            ssl_context = None

        # Create a request with the URL, file handle, and headers    
        req = Request(url, ovffile, headers)
        # Open the URL with the request
        urlopen(req, context=ssl_context)

    def start_timer(self):
        """
        A simple way to keep updating progress while the disks are transferred.
        """
        Timer(5, self.timer).start()

    def timer(self):
        """
        Update the progress and reschedule the timer if not complete.
        """
        try:
            # Get the current progress percentage
            prog = self.handle.progress()
            self.lease.Progress(prog)

             # Check if the lease is still active
            if self.lease.state not in [vim.HttpNfcLease.State.done,
                                        vim.HttpNfcLease.State.error]:
                self.start_timer()
            sys.stderr.write("Progress: %d%%\r" % prog)
        except Exception:  # Any exception means we should stop updating progress.
            pass


class FileHandle(object):
    """
    FileHandle class to manage local file operations.
    """

    def __init__(self, filename):
        self.filename = filename # Store the filename
        self.fh = open(filename, 'rb')

        #Get the size of the file
        self.st_size = os.stat(filename).st_size
        # Initialize offset for reading
        self.offset = 0

    # Ensure the file is closed when the object is deleted
    def __del__(self):
        self.fh.close()

    #Return the current read position in the file
    def tell(self):
        return self.fh.tell()

    def seek(self, offset, whence=0):
        """
        Move the read position to a new location in the file.
        whence: 0=absolute, 1=relative to current position, 2=relative to file's end.
        """
        if whence == 0:
            self.offset = offset # Absolute position
        elif whence == 1:
            self.offset += offset # Relative position
        elif whence == 2:
            self.offset = self.st_size - offset # Position relative to end

        return self.fh.seek(offset, whence) # Seek to the new position

    #Check if the file can be seeked.
    def seekable(self):
        return True

    #Read a specified amount of data from the file.
    def read(self, amount):
        self.offset += amount
        result = self.fh.read(amount)
        return result

    # A slightly more accurate percentage
    def progress(self):
        return int(100.0 * self.offset / self.st_size)


#WebHandle class to manage remote file operations over HTTP.
class WebHandle(object):
    def __init__(self, url):
        self.url = url  # Store the URL
        r = urlopen(url)  # Open the URL
        if r.code != 200:
            raise FileNotFoundError(url)
        
         # Convert headers to a dictionary
        self.headers = self._headers_to_dict(r)
        
        # Check if the server accepts byte ranges
        if 'accept-ranges' not in self.headers:
            raise Exception("Site does not accept ranges")
        
         # Get the content length from headers
        self.st_size = int(self.headers['content-length'])
        self.offset = 0


    #Convert HTTP headers to a dictionary format
    def _headers_to_dict(self, r):
        result = {}
        if hasattr(r, 'getheaders'): # If the response has getheaders method
            for n, v in r.getheaders():# Iterate through headers
                result[n.lower()] = v.strip()
        else:
            for line in r.info().headers:
                if line.find(':') != -1: # Check for valid header line
                    n, v = line.split(': ', 1)
                    result[n.lower()] = v.strip() # Store in dictionary
        
        return result # Return the headers as a dictionary


    #Return the current read position in the URL resource
    def tell(self):
        return self.offset

    def seek(self, offset, whence=0):

        """
        Move the read position in the remote file.
        whence: 0=absolute, 1=relative to current position, 2=relative to file's end.
        """
        if whence == 0:
            self.offset = offset
        elif whence == 1:
            self.offset += offset
        elif whence == 2:
            self.offset = self.st_size - offset
        return self.offset

    #Check if the remote resource can be seeked.
    def seekable(self):
        return True

    #Read a specified amount of data from the remote URL.
    def read(self, amount):
        start = self.offset # Start position for reading
        end = self.offset + amount - 1
        
        # Create a request for a byte range
        req = Request(self.url,
                      headers={'Range': 'bytes=%d-%d' % (start, end)})
        r = urlopen(req) # Perform the request
        self.offset += amount # Update the offset
        result = r.read(amount)  #Read the specified amount
        r.close() # Close the response
        return result

    # A slightly more accurate percentage
    def progress(self):
        """Return the current progress as a percentage for the remote file."""
        return int(100.0 * self.offset / self.st_size)

if __name__ == "__main__":
    # Execute the main function and exit with its return code
    sys.exit(main()) 