import network
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
