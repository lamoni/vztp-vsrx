#!/usr/bin/env python
"""
Written by Dann Bohn
Github: https://github.com/whereismyjetpack
Email: dannbohn@gmail.com
Clone a VM from template example
"""
from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect
import atexit
import argparse
import getpass
import ssl
from pprint import pprint
import subprocess
from jnpr.space import rest, async

def get_args():
    """ Get arguments from CLI """
    parser = argparse.ArgumentParser(
        description='Arguments for talking to vCenter')

    parser.add_argument('-s', '--host',
                        required=True,
                        action='store',
                        help='vSpehre service to connect to')

    parser.add_argument('-o', '--port',
                        type=int,
                        default=443,
                        action='store',
                        help='Port to connect on')

    parser.add_argument('-u', '--user',
                        required=True,
                        action='store',
                        help='Username to use')

    parser.add_argument('-p', '--password',
                        required=False,
                        action='store',
                        help='Password to use')

    parser.add_argument('-v', '--vm-name',
                        required=True,
                        action='store',
                        help='Name of the VM you wish to make')

    parser.add_argument('--template',
                        required=True,
                        action='store',
                        help='Name of the template/VM \
                            you are cloning from')

    parser.add_argument('--datacenter-name',
                        required=False,
                        action='store',
                        default=None,
                        help='Name of the Datacenter you\
                            wish to use. If omitted, the first\
                            datacenter will be used.')

    parser.add_argument('--vm-folder',
                        required=False,
                        action='store',
                        default=None,
                        help='Name of the VMFolder you wish\
                            the VM to be dumped in. If left blank\
                            The datacenter VM folder will be used')

    parser.add_argument('--datastore-name',
                        required=False,
                        action='store',
                        default=None,
                        help='Datastore you wish the VM to end up on\
                            If left blank, VM will be put on the same \
                            datastore as the template')

    parser.add_argument('--cluster-name',
                        required=False,
                        action='store',
                        default=None,
                        help='Name of the cluster you wish the VM to\
                            end up on. If left blank the first cluster found\
                            will be used')

    parser.add_argument('--resource-pool',
                        required=False,
                        action='store',
                        default=None,
                        help='Resource Pool to use. If left blank the first\
                            resource pool found will be used')

    parser.add_argument('--new-srx-ip',
                        required=True,
                        action='store',
                        help='The IP address that will be assigned to\
                            the newly-instantiated vSRX')

    parser.add_argument('--new-srx-root-password',
                        required=True,
                        action='store',
                        help='The root password that will be configured on\
                            the newly-instantiated vSRX')

    parser.add_argument('--new-srx-telnet-port',
                        required=True,
                        action='store',
                        help='The console telnet port that will be used to\
                            connect to the newly-instantiated SRX for bootstrap\
                            configuration')


    args = parser.parse_args()

    if not args.password:
        args.password = getpass.getpass(
            prompt='Enter password')

    return args


def wait_for_task(task):
    """ wait for a vCenter task to finish """
    task_done = False
    while not task_done:
        if task.info.state == 'success':
            return task.info.result

        if task.info.state == 'error':
            print "there was an error"
            pprint(task)
            task_done = True


def get_obj(content, vimtype, name):
    """
    Return an object by name, if name is None the
    first found object is returned
    """
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if name:
            if c.name == name:
                obj = c
                break
        else:
            obj = c
            break

    return obj


def clone_vm(
        content, template, vm_name, si,
        datacenter_name, vm_folder, datastore_name,
        cluster_name, resource_pool, telnet_port):
    """
    Clone a VM from a template/VM, datacenter_name, vm_folder, datastore_name
    cluster_name, resource_pool, and power_on are all optional.
    """

    # if none git the first one
    datacenter = get_obj(content, [vim.Datacenter], datacenter_name)

    if vm_folder:
        destfolder = get_obj(content, [vim.Folder], vm_folder)
    else:
        destfolder = datacenter.vmFolder

    if datastore_name:
        datastore = get_obj(content, [vim.Datastore], datastore_name)
    else:
        datastore = get_obj(
            content, [vim.Datastore], template.datastore[0].info.name)

    # if None, get the first one
    cluster = get_obj(content, [vim.ClusterComputeResource], cluster_name)

    if resource_pool:
        resource_pool = get_obj(content, [vim.ResourcePool], resource_pool)
    else:
        resource_pool = cluster.resourcePool

    # set relospec
    relospec = vim.vm.RelocateSpec()
    relospec.datastore = datastore

    clonespec = vim.vm.CloneSpec()
    clonespec.location = relospec
    clonespec.powerOn = True

    spec = vim.vm.ConfigSpec()

    dev_changes = []
    serial_spec = vim.vm.device.VirtualDeviceSpec()
    serial_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
    serial_spec.device = vim.vm.device.VirtualSerialPort()
    serial_spec.device.backing = vim.vm.device.VirtualSerialPort.URIBackingInfo()
    serial_spec.device.backing.direction = "client"
    serial_spec.device.backing.serviceURI = "tcp://a-inf-vansible1:13370"
    #serial_spec.device.backing.serviceURI = "vSPC.py"
    #serial_spec.device.backing.proxyURI = " telnet://:" + telnet_port
    dev_changes.append(serial_spec)
    spec.deviceChange = dev_changes

    clonespec.config = spec

    print "Cloning VM with new virtual serial port..."
    task = template.Clone(folder=destfolder, name=vm_name, spec=clonespec)
    wait_for_task(task)


def update_serial_port(vm_obj):
    """
    :param vm_obj: Virtual Machine Object
    :param si: Service Instance
    :return: True if success
    """
    nic_label = 'Serial port 1'
    virtual_nic_device = None
    for dev in vm_obj.config.hardware.device:
        if isinstance(dev, vim.vm.device.VirtualSerialPort) \
                and dev.deviceInfo.label == nic_label:
            virtual_nic_device = dev

    virtual_nic_spec = vim.vm.device.VirtualDeviceSpec()
    virtual_nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
    virtual_nic_spec.device = virtual_nic_device
    virtual_nic_spec.device.key = virtual_nic_device.key
    virtual_nic_spec.device.backing = virtual_nic_device.backing
    virtual_nic_spec.device.backing.direction = "server"
    virtual_nic_spec.device.backing.serviceURI = "tcp://a-inf-vansible1:12345"
    dev_changes = []
    dev_changes.append(virtual_nic_spec)
    spec = vim.vm.ConfigSpec()
    spec.deviceChange = dev_changes
    task = vm_obj.ReconfigVM_Task(spec=spec)
    wait_for_task(task)

    return True

def main():
    """
    Let this thing fly
    """
    args = get_args()
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    context.verify_mode = ssl.CERT_NONE

    # connect this thing
    si = SmartConnect(
        host=args.host,
        user=args.user,
        pwd=args.password,
        port=args.port,
        sslContext=context)
    # disconnect this thing
    atexit.register(Disconnect, si)

    content = si.RetrieveContent()
    template = None

    template = get_obj(content, [vim.VirtualMachine], args.template)

    if template:
        clone_vm(
            content, template, args.vm_name, si,
            args.datacenter_name, args.vm_folder,
            args.datastore_name, args.cluster_name,
            args.resource_pool, args.new_srx_telnet_port)

        print "New VM Info: %s - %s - %s" % (args.new_srx_ip, args.new_srx_root_password, args.new_srx_telnet_port)

    else:
        print "Cloning VM Error: Template/VM not found"



    print "Initiating console connection for bootstrap configuration...."
    # Run the expect script for configuring the devices with their IP address
    # cmd = ['/var/www/console-config.exp', args.new_srx_ip, args.new_srx_root_password, args.new_srx_telnet_port]
    # subprocess.Popen(cmd).wait()
    cmd = ['/var/www/console-config.exp', args.new_srx_ip, args.new_srx_root_password, "13370", args.vm_name]
    subprocess.Popen(cmd).wait()


    print "Redirecting console port elsewhere..."
    content = si.RetrieveContent()

    vm_obj = get_obj(content, [vim.VirtualMachine], args.vm_name)

    if vm_obj:
        update_serial_port(vm_obj)
        print 'VM Serial Port successfully redirected'

    ############################

    # print "Triggering Junos Space discovery"
    #
    # s = rest.Space(url='https://10.180.21.67',
    #                user='super',
    #                passwd='Am3rL@bAm3rL@b')
    # devs = s.device_management.devices.get()
    # result = s.device_management.discover_devices.post(
    #     ipAddress=args.new_srx_ip,
    #     sshCredential={'userName':'root', 'password': args.new_srx_root_password})
    #
    # print "Finished Space Discovery"




# start this thing
if __name__ == "__main__":
    main()