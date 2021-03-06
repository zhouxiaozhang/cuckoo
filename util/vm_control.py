from __future__ import print_function
import subprocess
import sys
import os
import signal
import time
import errno
import threading

VBOXMANAGE_BIN = "VBoxManage"


def info_print(msg, ret, out):
    if ret == 0:
        print("%s %s" % (msg, ret))
    else:
        print("%s %s. %s" % (msg, ret, out))


def execute(*args, **kwargs):

    #print(args)

    completed_process = subprocess.run(
        *args,
        timeout=10,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        **kwargs
    )
    return completed_process.returncode, completed_process.stdout

    # def kill(process):
    #     process.kill()
    #     os.kill(process.pid, signal.SIGKILL)
    #     subprocess.run("kill -9 %d" % process.pid, shell=True)

    # process = subprocess.Popen(stdout=subprocess.PIPE, stderr=subprocess.STDOUT, *args, **kwargs)
    #
    # my_timer = threading.Timer(20, kill, [process])
    # ret = 1
    # try:
    #     my_timer.start()
    #     output, _ = process.communicate()
    #     ret = process.poll()
    # finally:
    #     my_timer.cancel()
    #
    # return ret, output


def create_if():
    ret, out = execute([
            VBOXMANAGE_BIN,
            "hostonlyif",
            "create",
    ])
    info_print("Create Hostonlyif. ", ret, out)

    ret, out = execute([
            VBOXMANAGE_BIN,
            "hostonlyif"
            "ipconfig"
            "vboxnet0"
            "--ip",
            "192.168.56.1"
            "--netmask 255.255.255.0"
    ])
    info_print("Config Hostonlyif. ", ret, out)

    ret, out = execute([
        VBOXMANAGE_BIN,
        "dhcpserver",
        "modify",
        "--ifname",
        "vboxnet0",
        "--disable",
    ])
    info_print("Closing DHCP server. ", ret, out)


def check_if():
    ret, out = execute([
        VBOXMANAGE_BIN,
        "list",
        "hostonlyifs",
    ])
    if out == "":
        create_if()


def clone_vm(from_vm_name, new_vm_name):
    print("Cloning vm from %s to %s" % (from_vm_name, new_vm_name))

    ret, out = execute([
        VBOXMANAGE_BIN,
        "clonevm",
        from_vm_name,
        "--snapshot",
        "ReadytoRun",
        "--options",
        "link",
        "--name",
        new_vm_name,
        "--register",
    ])
    info_print("Clone VM. ", ret, out)


def wait_for_vm_ready(vm_name):
    print("Wait for vm")
    ret = 1

    while ret != 0:
        time.sleep(5)
        cmd = [
            VBOXMANAGE_BIN,
            'guestcontrol',
            vm_name,
            '--username',
            'Cuckoo',
            'run',
            '--exe',
            '"c:\\Windows\\system32\\ipconfig.exe"',
            ]
        cmd = " ".join(cmd)
        ret, out = execute(cmd, shell=True)
        info_print("Waiting for VM. ", ret, out)

    print("Wait for vm, finish")
    time.sleep(5)
    return


def reboot_vm(vm_name):
    ret = 1
    while ret != 0:
        time.sleep(10)
        cmd = [
            VBOXMANAGE_BIN,
            'guestcontrol',
            vm_name,
            '--username',
            'Cuckoo',
            'run',
            '--exe',
            '"c:\\Python27\\python.exe"',
            '--',
            '"/c"',
            '"c:\\Users\\cuckoo\\sudo.py"',
            '"shutdown"',
            '"-r"',
            '"-t"',
            '"0"',
        ]
        cmd = " ".join(cmd)
        ret, out = execute(cmd, shell=True)
        info_print("Rebooting VM. ", ret, out)

    time.sleep(10)


def config_vm(vm_name, ip_address):
    print("Configuring vm %s, %s" % (vm_name, ip_address))

    ret, out = execute([
        VBOXMANAGE_BIN,
        "startvm",
        vm_name,
        "--type",
        "headless",
    ])
    info_print("Start VM. ", ret, out)

    wait_for_vm_ready(vm_name)

    cmd = [
        VBOXMANAGE_BIN,
        'guestcontrol',
        vm_name,
        '--username',
        'Cuckoo',
        'run',
        '--exe',
        '"c:\\Python27\\python.exe"',
        '--',
        '"/c"',
        '"c:\\Users\\cuckoo\\sudo.py"',
        '"netsh"',
        '"interface"',
        '"ipv4"',
        '"set"',
        '"address"',
        '"\\\"\\\"Local"',
        '"Area"',
        '"Connection\\\"\\\""',
        '"static"',
        '"%s"' % ip_address,
        '"255.255.255.0"',
        '"192.168.56.1"',
    ]
    cmd = " ".join(cmd)
    ret, out = execute(cmd, shell=True)
    info_print("Config VM's IP addr. ", ret, out)

    cmd = [
        VBOXMANAGE_BIN,
        'guestcontrol',
        vm_name,
        '--username',
        'Cuckoo',
        'run',
        '--exe',
        '"c:\\Python27\\python.exe"',
        '--',
        '"/c"',
        '"c:\\Users\\cuckoo\\sudo.py"',
        '"netsh"',
        '"interface"',
        '"ipv4"',
        '"set"',
        '"dns"',
        '"\\\"\\\"Local"',
        '"Area"',
        '"Connection\\\"\\\""',
        '"static"',
        '"223.5.5.5"',
        ]
    cmd = " ".join(cmd)
    ret, out = execute(cmd, shell=True)
    info_print("Config VM's DNS addr. ", ret, out)

    wait_for_vm_ready(vm_name)

    reboot_vm(vm_name)

    wait_for_vm_ready(vm_name)

    cmd = [
        VBOXMANAGE_BIN,
        'guestcontrol',
        vm_name,
        '--username',
        'Cuckoo',
        'run',
        '--exe',
        '"c:\\Python27\\python.exe"',
        '--',
        '"/c"',
        '"c:\\Users\\cuckoo\\sudo.py"',
        '"cmd"',
        '"/c"',
        '"start"',
        '"c:\\Python27\\python.exe"',
        '"c:\\Users\\cuckoo\\agent_service_starter.py"',
    ]
    cmd = " ".join(cmd)
    ret, out = execute(cmd, shell=True)
    info_print("Start VM's agent. ", ret, out)

    cmd = [
        VBOXMANAGE_BIN,
        'guestcontrol',
        vm_name,
        '--username',
        'Cuckoo',
        'run',
        '--exe',
        '"c:\\Python27\\python.exe"',
        '--',
        '"/c"',
        '"c:\\Users\\cuckoo\\change_display.py"',
        '"set"',
        '"1920"',
        '"1440"',
        '"32"',
    ]
    cmd = " ".join(cmd)
    ret, out = execute(cmd, shell=True)
    info_print("Change VM's resolution. ", ret, out)

    time.sleep(20)

    ret, out = execute([
        VBOXMANAGE_BIN,
        'snapshot',
        vm_name,
        'take',
        "ReadytoRun",
    ])
    info_print("Taking VM's snapshot. ", ret, out)

    ret, out = execute([
        VBOXMANAGE_BIN,
        'controlvm',
        vm_name,
        "poweroff",
    ])
    info_print("Shotdown VM. ", ret, out)

    ret, out = execute([
        VBOXMANAGE_BIN,
        'snapshot',
        vm_name,
        'restore',
        "ReadytoRun",
    ])
    info_print("Restoring VM's snapshot. ", ret, out)


def create_vm_from_vdi(vm_name, vdi_path):
    print("Creating vm %s, from vid: %s" % (vm_name, vdi_path))
    check_if()
    ret, out = execute([
        VBOXMANAGE_BIN,
        "createvm",
        "--name",
        vm_name,
        "--ostype",
        "Windows7_64",
        "--register"
    ])
    info_print("Create VM. ", ret, out)

    ret, out = execute([
        VBOXMANAGE_BIN,
        "modifyvm",
        vm_name,
        "--memory",
        "1024",
    ])
    info_print("Modify VM's memory. ", ret, out)

    ret, out = execute([
        VBOXMANAGE_BIN,
        "modifyvm",
        vm_name,
        "--vram",
        "64",
    ])
    info_print("Modify VM's video memory. ", ret, out)

    ret, out = execute([
        VBOXMANAGE_BIN,
        "storagectl",
        vm_name,
        "--name",
        "SATA",
        "--add",
        "sata",
        "--portcount",
        "1",
        "--bootable",
        "on"
    ])
    info_print("Modify VM's storage. ", ret, out)

    cmd = [
        VBOXMANAGE_BIN,
        "storageattach",
        vm_name,
        "--storagectl",
        "SATA",
        "--port",
        "0",
        "--device",
        "0",
        "--type",
        "hdd",
        "--medium",
        vdi_path,
        "--setuuid",
        '""',
    ]
    cmd = " ".join(cmd)
    ret, out = execute(cmd, shell=True)
    info_print("Attach VM's storage. ", ret, out)

    ret, out = execute([
        VBOXMANAGE_BIN,
        "modifyvm",
        vm_name,
        "--nic1",
        "hostonly",
        "--hostonlyadapter1",
        "vboxnet0",
    ])
    info_print("Modify VM's net adapter. ", ret, out)


def main():

    if sys.argv[1] == "create":
        vdi_path = sys.argv[2]
        print("Vdi path: %s" % vdi_path)
        create(vdi_path)

    elif sys.argv[1] == "copy":
        num = int(sys.argv[2])
        print("Copying %d vms" % num)
        copy(num)
    else:
        exit(-1)


def create(vdi_path):
    create_vm_from_vdi(
        "Cuckoo0",
        vdi_path
    )
    config_vm("Cuckoo0", "192.168.56.110")


def copy(copy_num):
    for i in range(1, copy_num + 1):
        clone_vm("Cuckoo0", "Cuckoo%d" % i)
        config_vm("Cuckoo%d" % i, "192.168.56.%d" % (110 + i))
        print("-----")


if __name__ == "__main__":
    main()
