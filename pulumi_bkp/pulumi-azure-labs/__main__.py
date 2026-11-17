import network
import vm
import pulumi
from pulumi_azure_native import resources

env = pulumi.get_stack()

resource_group = resources.ResourceGroup(
    "rg",
    resource_group_name=f"rg-lab-{env}-sk",
    tags={"environment": env, "managed-by": "pulumi"},
)

pulumi.export("resource_group", resource_group.name)
pulumi.export("location", resource_group.location)

#network.create_network(resource_group)
vnet, web_subnet, app_subnet, db_subnet = network.create_network(resource_group)
pulumi.export("vnet_name", vnet.name)
pulumi.export("web_subnet_id", web_subnet.id)
pulumi.export("app_subnet_id", app_subnet.id)
pulumi.export("db_subnet_id", db_subnet.id)
#vm.create_vm(resource_group, web_subnet)

public_ip, virtual_machine = vm.create_vm(resource_group, web_subnet)
pulumi.export("public_ip", public_ip.ip_address)
pulumi.export("ssh_command", public_ip.ip_address.apply(lambda ip: f"ssh -i ~/.ssh/lab_vm azureuser@{ip}"))
