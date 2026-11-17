import pulumi
import pulumi_azure_native as azure_native


def create_vm(resource_group, subnet):
    config = pulumi.Config()

    public_ip = azure_native.network.PublicIPAddress(
        "pip",
        public_ip_address_name="pip-lab-dev-sk",
        resource_group_name=resource_group.name,
        sku=azure_native.network.PublicIPAddressSkuArgs(name="Standard"),
        public_ip_allocation_method="Static",
    )
    nic = azure_native.network.NetworkInterface(
        "nic",
        network_interface_name="nic-lab-dev-sk",
        resource_group_name=resource_group.name,
        ip_configurations=[
            azure_native.network.NetworkInterfaceIPConfigurationArgs(
                name="ipconfig1",
                subnet=azure_native.network.SubnetArgs(id=subnet.id),
                public_ip_address=azure_native.network.PublicIPAddressArgs(id=public_ip.id),
                private_ip_allocation_method="Dynamic",
            )
        ],
    )
    vm_size = config.get("vmSize") or "Standard_B1s"
    ssh_public_key = config.require("sshPublicKey")

    virtual_machine = azure_native.compute.VirtualMachine(
        "vm",
        vm_name="vm-lab-dev-ks",
        resource_group_name=resource_group.name,
        # 1. Hardware: size
        hardware_profile=azure_native.compute.HardwareProfileArgs(
            vm_size=vm_size,
        ),
        # 2. Network: attach the NIC from Part B
        network_profile=azure_native.compute.NetworkProfileArgs(
            network_interfaces=[
                azure_native.compute.NetworkInterfaceReferenceArgs(
                    id=nic.id,
                    primary=True,
                    delete_option="Delete",
                )
            ],
        ),
        # 3. Storage: Ubuntu 24.04 image and OS disk
        storage_profile=azure_native.compute.StorageProfileArgs(
            image_reference=azure_native.compute.ImageReferenceArgs(
                publisher="Canonical",
                offer="ubuntu-24_04-lts",
                sku="server",
                version="latest",
            ),
            os_disk=azure_native.compute.OSDiskArgs(
                create_option="FromImage",
                delete_option="Delete",
                managed_disk=azure_native.compute.ManagedDiskParametersArgs(
                    storage_account_type="Standard_LRS",
                ),
            ),
        ),
        # 4. OS: admin user and SSH key, no passwords
        os_profile=azure_native.compute.OSProfileArgs(
            computer_name="vm-lab-dev-sk",
            admin_username="azureuser",
            linux_configuration=azure_native.compute.LinuxConfigurationArgs(
                disable_password_authentication=True,
                ssh=azure_native.compute.SshConfigurationArgs(
                    public_keys=[
                        azure_native.compute.SshPublicKeyArgs(
                            path="/home/azureuser/.ssh/authorized_keys",
                            key_data=ssh_public_key,
                        )
                    ],
                ),
            ),
        ),
    )

    return public_ip, virtual_machine
