import pulumi
import pulumi_azure_native as azure_native


def create_network(resource_group):
    config = pulumi.Config()

    # Exercise 2: VNet CIDR from config, with a default
    vnet_cidr = config.get("vnetCidr") or "10.0.0.0/16"

    web_cidr = "10.0.1.0/24"
    app_cidr = "10.0.2.0/24"
    db_cidr = "10.0.3.0/24"

    vnet = azure_native.network.VirtualNetwork(
        "vnet",
        virtual_network_name="vnet-lab-dev",
        resource_group_name=resource_group.name,
        address_space=azure_native.network.AddressSpaceArgs(
            address_prefixes=[vnet_cidr],
        ),
    )
    # Exercise 3: SSH source from config. "*" = any source (lab default).
    ssh_source = config.get("sshSource") or "*"

    # Lower priority number = evaluated first.
    def inbound_allow(name, priority, port, source):
        return azure_native.network.SecurityRuleArgs(
            name=name,
            priority=priority,
            direction="Inbound",
            access="Allow",
            protocol="Tcp",
            source_port_range="*",
            destination_port_range=port,
            source_address_prefix=source,
            destination_address_prefix="*",
        )

    nsg_web = azure_native.network.NetworkSecurityGroup(
        "nsg-web",
        network_security_group_name="nsg-web-dev-sk",
        resource_group_name=resource_group.name,
        security_rules=[
            inbound_allow("allow-http", 100, "80", "*"),
            inbound_allow("allow-https", 110, "443", "*"),
            inbound_allow("allow-ssh", 120, "22", ssh_source),
        ],
    )

    web_subnet = azure_native.network.Subnet(
        "snet-web",
        subnet_name="snet-web-sk",
        resource_group_name=resource_group.name,
        virtual_network_name=vnet.name,
        address_prefix=web_cidr,
        network_security_group=azure_native.network.NetworkSecurityGroupArgs(
            id=nsg_web.id,
        ),
    )
    app_subnet = azure_native.network.Subnet(
        "snet-app",
        subnet_name="snet-app-sk",
        resource_group_name=resource_group.name,
        virtual_network_name=vnet.name,
        address_prefix=app_cidr,
        opts=pulumi.ResourceOptions(depends_on=[web_subnet]),
    )
    nsg_db = azure_native.network.NetworkSecurityGroup(
        "nsg-db",
        network_security_group_name="nsg-db-dev-sk",
        resource_group_name=resource_group.name,
        security_rules=[
            azure_native.network.SecurityRuleArgs(
                name="allow-from-app",
                priority=100,
                direction="Inbound",
                access="Allow",
                protocol="*",
                source_port_range="*",
                destination_port_range="*",
                source_address_prefix=app_cidr,
                destination_address_prefix="*",
            ),
            azure_native.network.SecurityRuleArgs(
                name="deny-all-inbound",
                priority=4096,
                direction="Inbound",
                access="Deny",
                protocol="*",
                source_port_range="*",
                destination_port_range="*",
                source_address_prefix="*",
                destination_address_prefix="*",
            ),
        ],
    )

    db_subnet = azure_native.network.Subnet(
        "snet-db",
        subnet_name="snet-db-sk",
        resource_group_name=resource_group.name,
        virtual_network_name=vnet.name,
        address_prefix=db_cidr,
        network_security_group=azure_native.network.NetworkSecurityGroupArgs(
            id=nsg_db.id,
        ),
        opts=pulumi.ResourceOptions(depends_on=[app_subnet]),
    )

    return vnet, web_subnet, app_subnet, db_subnet
