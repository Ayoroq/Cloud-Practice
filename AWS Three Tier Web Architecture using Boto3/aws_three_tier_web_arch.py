from typing import Protocol
import boto3
from colorama import init

client = boto3.client('ec2')

ec2 = boto3.resource('ec2')

client_db = boto3.client('rds')

elb = boto3.client('elbv2')


# A class that creates a VPC
class _vpc:
    """ This is a class that creates a VPC. 
    It needs cidr block and the vpc name as parameters.
    It aslo contains a funtion create_vpc that needs to be called for the 
    VPC to be created """

    def __init__(self, cidr_block,vpc_name) -> None:
        self.cidr_block = cidr_block
        self.name = vpc_name

    def create_vpc(self):
        response = client.create_vpc(
            CidrBlock = self.cidr_block,
        )
        self.id = response['Vpc']['VpcId']


        client.create_tags(
            Resources = [self.id],
            Tags = [
                {
                    'Key' : 'Name',
                    'Value' :self.name  
                },
            ]
        )
        print(self.name,self.id)


vpc = _vpc('192.168.0.0/16','awsthreetierworkshop')
vpc.create_vpc()

# A class that creates subnets
class _subnet():
    """ This is a class that's used to create s subnet
        it takes in the Name, Availability zone, vpcid and the Cidr block as values.
        It contains a create_subnet method that's used to create the subnets upon calling it
    """
    def __init__(self,Name,AvailabilityZone,VpcId,CidrBlock):
        self.name = Name
        self.AvailabilityZone = AvailabilityZone
        self.VpcId = VpcId
        self.CidrBlock = CidrBlock
    
    # Creating the subnet
    def create_subnet(self):
        subnet = ec2.create_subnet(
            AvailabilityZone = self.AvailabilityZone,
            CidrBlock = self.CidrBlock,
            VpcId = self.VpcId
        )

        # adding the name to the subnet
        subnet.create_tags(
            Tags = [
                {
                    'Key': 'Name',
                    'Value': self.name
                },
            ]
        )

        self.id = subnet.id

# Creating the different subnets needed.
public_subnet_a = _subnet('Public_Subnet_AZ_a','us-east-1a',vpc.id,'192.168.0.0/19')
private_subnet_a = _subnet('Private_Subnet_AZ_a','us-east-1a',vpc.id,'192.168.32.0/19')
private_db_subnet_a = _subnet('Private_DB_Subnet_AZ_a','us-east-1a',vpc.id,'192.168.64.0/19')
public_subnet_b = _subnet('Public_Subnet_AZ_b','us-east-1b',vpc.id,'192.168.96.0/19')
private_subnet_b = _subnet('Private_Subnet_AZ_b','us-east-1b',vpc.id,'192.168.128.0/19')
private_db_subnet_b = _subnet('Private_DB_Subnet_AZ_b','us-east-1b',vpc.id,'192.168.160.0/19')

public_subnet_a.create_subnet()
private_subnet_a.create_subnet()
private_db_subnet_a.create_subnet()
public_subnet_b.create_subnet()
private_subnet_b.create_subnet()
private_db_subnet_b.create_subnet()


#creating an internet gateway
class internet_gateway():
    """ This class creates an internet gateway and attaches it to 
     a vpc. It requires the name of the the gateway and the vpc id
     a method create_internet_gateway() needs to be called on the instance object  """
    def __init__(self, name, vpc_id):
        self.name = name
        self.vpc_id = vpc_id

    # Creates the internet gateway
    def create_internet_gateway(self):
        flo = client.create_internet_gateway()
        self.id = flo['InternetGateway']['InternetGatewayId']

        #attaches the name to the interbet gateway
        client.create_tags(
            Resources = [self.id],
            Tags = [
                {
                    'Key' : 'Name',
                    'Value' :self.name  
                },
            ]
        )

        # attaches the internet gateway to the vpc
        flo = client.attach_internet_gateway(
            InternetGatewayId = self.id,
            VpcId = self.vpc_id
        )

igw = internet_gateway('three-tier-igw',vpc.id)
igw.create_internet_gateway()


class nat_gateway():
    """ This class is used to create a nat gateway.\n
     It attaches an elastic Ip address to the nat gateway and
     the needed parameters are the elastic IP name, nat gateway name and the subnet id.\n
     You need to call the method create_nat_gateway() on the instance object """

    def __init__(self,elastic_ip_name,nat_name,subnet_id):
        self.name = nat_name
        self.subnet_id = subnet_id
        self.elastic_ip_name = elastic_ip_name

    # Creating an nat gateway
    def create_nat_gateway(self):
        #creating the elastic ip address
        allocate = client.allocate_address(Domain = 'vpc')
        self.allocation_id = allocate['AllocationId']

        #attaches the name to the elastic_ip
        client.create_tags(
            Resources = [self.allocation_id],
            Tags = [
                {
                    'Key' : 'Name',
                    'Value' :self.elastic_ip_name  
                },
            ]
        ) 

        # Creating the nat_gateway and attaching the elastic ip created above
        nat = client.create_nat_gateway(
            AllocationId = self.allocation_id,
            ConnectivityType = 'public',
            SubnetId = self.subnet_id
        )

        self.id = nat['NatGateway']['NatGatewayId']

        #attaches the name to the nat_gateway
        client.create_tags(
            Resources = [self.id],
            Tags = [
                {
                    'Key' : 'Name',
                    'Value' :self.name
                },
            ]
        ) 


# Creating the instance objects for the nat_gateways
nat_az_a = nat_gateway('elas_az_a','nat_az_a',public_subnet_a.id)
nat_az_b = nat_gateway('elas_az_b','nat_az_b',public_subnet_b.id)


# calling the instance methods
nat_az_a.create_nat_gateway()
nat_az_b.create_nat_gateway()



#Creating a route table
class route_table():
    """ This is a class used to create a route table.
     After the route table has been created, it associated the subnet and adds a route to nat or internet gateway\n
     It takes in the name,subnet id, internet_or_nat_gateway_id and vpc id as parameters
     You have to call the method create_route_table() on the object.  """
    def __init__(self, name, subnet_id, internet_or_nat_gateway_id, vpc_id):
        self.name = name
        self.int_gate_id = internet_or_nat_gateway_id
        self.subnet_id = subnet_id
        self.vpc_id = vpc_id

    def create_route_table(self):
        # creating the route table and adding it to the Vpc
        route_table = client.create_route_table(
            VpcId = self.vpc_id
        )
        self.id = route_table['RouteTable']['RouteTableId']

        #attaches the name to the route_table
        client.create_tags(
            Resources = [self.id],
            Tags = [
                {
                    'Key' : 'Name',
                    'Value' :self.name
                },
            ]
        )

        #Associating the route table to the subnet and gateway
        client.create_route(
            DestinationCidrBlock='0.0.0.0/0',
            RouteTableId = self.id,
            GatewayId = self.int_gate_id
        )

        client.associate_route_table(
            RouteTableId = self.id,
            SubnetId = self.subnet_id
        )

Public_RT = route_table('PublicRouteTable',public_subnet_a.id,igw.id,vpc.id)
Public_RT.create_route_table()
# The second connection to the public subnet 4 was created through the UI

# Creating the route table for for each app layer private subnet
Private_RT_az_a = route_table('private_rt_az_a',private_subnet_a.id,nat_az_a.id,vpc.id)
Private_RT_az_b = route_table('private_rt_az_b',private_subnet_b.id,nat_az_b.id,vpc.id)

Private_RT_az_a.create_route_table()
Private_RT_az_b.create_route_table()


#Creating security groups
#sg = client.describe_security_groups(GroupIds = ['sg-0facb95b9c951bf49'])
#print(sg)

class security_groups:

    def __init__(self, name, vpc_id, description):
        self.name = name
        self.vpc_id = vpc_id
        self.description = description

    def create_sg(self):
        sg = client.create_security_group(
            Description = self.description,
            GroupName = self.name,
            VpcId = self.vpc_id
        )
        self.id = sg['GroupId']

#creating the sg for the internet facing load balancer
internet_facing_lb_sg = security_groups('internet_facing_lb_sg',vpc.id,'External load balancer security group')
internet_facing_lb_sg.create_sg()

#Adding the inbound rule
sg_attach = client.authorize_security_group_ingress(
    GroupId = internet_facing_lb_sg.id,
    IpPermissions = [
        {
            'FromPort':80,
            'IpProtocol': 'tcp',
            'IpRanges': [
                {
                    'CidrIp': '65.92.12.205/32',
                },
            ],
            'ToPort': 80,
        },
    ],
)

#creating the security group for the web tier
web_tier_sg = security_groups('WebTierSg',vpc.id,'SG for the web tier')
web_tier_sg.create_sg()

#Adding the inbound rule
sg_attach_web = client.authorize_security_group_ingress(
    GroupId = web_tier_sg.id,
    IpPermissions = [
        {
            'FromPort':80,
            'IpProtocol': 'tcp',
            'IpRanges': [
                {
                    'CidrIp': '65.92.12.205/32',
                },
            ],
            'ToPort': 80,
        },
        {
           'FromPort': 80,
           'IpProtocol': 'tcp',
           'ToPort': 80,
           'UserIdGroupPairs':[
               {
                   'GroupId': internet_facing_lb_sg.id,
               },
           ],
        },
    ],
)


#creating internal load balancer sg
internal_lb_sg = security_groups('internal_lb_sg',vpc.id,'SG for the internal load balancer')
internal_lb_sg.create_sg()

#Adding the inbound rule
sg_attach_internal = client.authorize_security_group_ingress(
    GroupId = internal_lb_sg.id,
    IpPermissions = [
        {
           'FromPort': 80,
           'IpProtocol': 'tcp',
           'ToPort': 80,
           'UserIdGroupPairs':[
               {
                   'GroupId': web_tier_sg.id,
               },
           ],
        },
    ],
)


#creating the private instance sg
private_inst_sg = security_groups('private_inst_sg',vpc.id,'SG for the private app tier sg')
private_inst_sg.create_sg()

#Adding the inbound rule
sg_attach_private = client.authorize_security_group_ingress(
    GroupId = private_inst_sg.id,
    IpPermissions = [
        {
            'FromPort':4000,
            'IpProtocol': 'tcp',
            'IpRanges': [
                {
                    'CidrIp': '65.92.12.205/32',
                },
            ],
            'ToPort': 4000,
        },
        {
           'FromPort': 4000,
           'IpProtocol': 'tcp',
           'ToPort': 4000,
           'UserIdGroupPairs':[
               {
                   'GroupId': internal_lb_sg.id,
               },
           ],
        },
    ],
)


#creating the database sg
db_sg = security_groups('db_sg',vpc.id,'SG for our databases')
db_sg.create_sg()

#Adding the inbound rule
sg_attach_db = client.authorize_security_group_ingress(
    GroupId = db_sg.id,
    IpPermissions = [
        {
           'FromPort': 3306,
           'IpProtocol': 'tcp',
           'ToPort': 3306,
           'UserIdGroupPairs':[
               {
                   'GroupId': private_inst_sg.id,
               },
           ],
        },
    ],
)


# PART 2

# Creating the db_subnet_ids
class db_subnet_group:
    
    def __init__(self, name, description, subnet_ids = []):
        self.name = name
        self.description = description
        self.subnet_ids = subnet_ids
 

    def create_db_subnet_group(self):
        db_subnet = client_db.create_db_subnet_group(
            DBSubnetGroupName = self.name,
            DBSubnetGroupDescription = self.description,
            SubnetIds = self.subnet_ids
        )

three_tier_db_sb_grp = db_subnet_group('three_tier_db_subnet_group','Subnet group for the database layer of the architecture', [private_db_subnet_a.id,private_db_subnet_b.id])
three_tier_db_sb_grp.create_db_subnet_group()


# Creating the DB cluster
db_cluster = client_db.create_db_cluster(
    AvailabilityZones=[
        'us-east-1a', 'us-east-1b',
    ],
    DatabaseName = 'db',
    DBClusterIdentifier = 'database',
    Engine = 'aurora-mysql',
    EngineVersion = '8.0.mysql_aurora.3.04.1',
    MasterUsername = 'admin',
    MasterUserPassword = 'dbpassword',
    VpcSecurityGroupIds = [db_sg.id],
    DBSubnetGroupName = three_tier_db_sb_grp.name, #three_tier_db_sb_grp,
)

# Creating the DB instance
db_instance = client_db.create_db_instance(
    DBInstanceIdentifier = 'db',
    DBClusterIdentifier = db_cluster['DBCluster']['DBClusterIdentifier'],
    DBInstanceClass = 'db.t3.medium',
    Engine = 'aurora-mysql',
    EngineVersion = '8.0.mysql_aurora.3.04.1',
    AvailabilityZone = 'us-east-1a'
)

# Creating the second DB instance
db_instance = client_db.create_db_instance(
    DBInstanceIdentifier = 'db2',
    DBClusterIdentifier = db_cluster['DBCluster']['DBClusterIdentifier'],
    DBInstanceClass = 'db.t3.medium',
    Engine = 'aurora-mysql',
    EngineVersion = '8.0.mysql_aurora.3.04.1',
    AvailabilityZone = 'us-east-1b',
)

# Part 3
# App Tier Instance Deployment

# code to create the app tier instance
ec2_create = ec2.create_instances(
    BlockDeviceMappings = [ 
        {
        'DeviceName': '/dev/xvda',
        'Ebs': {
            'DeleteOnTermination': True,
            'Iops': 3000,
            'VolumeSize': 8,
            'VolumeType': 'gp3',
            'Throughput': 125
            },
        },
    ],
    ImageId = 'ami-0cf10cdf9fcd62d37',
    InstanceType = 't2.micro',
    MaxCount = 1,
    MinCount = 1,
    IamInstanceProfile={
        'Name': 'ec2_role'
    },
    SecurityGroupIds = [
        private_inst_sg.id,
    ],
    SubnetId = private_subnet_a.id,
)

print(ec2_create[0].id)

# Naming the instance
client.create_tags(
            Resources = [ec2_create[0].id],
            Tags = [
                {
                    'Key' : 'Name',
                    'Value' : 'App Layer'
                },
            ]
        )



# Part 4
#creating an AMI from a running instance
ami = client.create_image(
    BlockDeviceMappings=[
        {
            'DeviceName': '/dev/xvda',
            'Ebs': {
                'DeleteOnTermination': True,
                'VolumeSize': 8,
            },
        },   
    ],
    Description = 'App Tier',
    InstanceId = ec2_create[0].id,
    Name = 'AppTierImage',
    NoReboot = True,
)

print(ami)


# Creating target group
app_target_group = elb.create_target_group(
    Name = 'AppTierTagertGroup',
    Protocol = 'HTTP',
    Port = 4000,
    VpcId = vpc.id,
    HealthCheckProtocol = 'HTTP',
    HealthCheckEnabled = True,
    HealthCheckPath = '/health',
    TargetType = 'instance'
)

print(app_target_group)

# Creating Load balancer
app_lb = elb.create_load_balancer(
    Name = 'app-tier-internal-lb',
    Subnets = [private_subnet_a.id,private_subnet_b.id], #private_subnet_a.id,private_subnet_b.id
    SecurityGroups = [internal_lb_sg.id], #
    Scheme = 'internal',
    Type = 'application',
    IpAddressType = 'ipv4'
)
print(app_lb)

# Creating listener to the app load balancer
app_listener = elb.create_listener(
    DefaultActions=[
        {
            'TargetGroupArn': app_target_group['TargetGroups'][0]['TargetGroupArn'], #app_target_group ARN
            'Type': 'forward',
        },
    ],
    LoadBalancerArn = app_lb['LoadBalancers'][0]['LoadBalancerArn'], #app_lb ARN
    Port=80,
    Protocol='HTTP',
)



# Creating the launch template for the app tier instance

app_launch_template = client.create_launch_template(
    LaunchTemplateName = 'App_tier_template',
    LaunchTemplateData = {
        'ImageId': ami['ImageId'], #ami.id
        'InstanceType': 't2.micro',
        'IamInstanceProfile': {
            'Arn': 'arn:aws:iam::851725412064:instance-profile/ec2_role',
            #'Name': 'ec2_role'
        },
        'SecurityGroupIds': [private_inst_sg.id], #private_inst_sg.id
        'BlockDeviceMappings':[
            {   
                'DeviceName': '/dev/xvda',
                'Ebs': {
                'VolumeSize': 8,
                'VolumeType': 'gp2',
            },
            },
        ],
    },
)


# Creating the private instance auto scaling group

auto_sc = boto3.client('autoscaling')

auto_scaling_grp = auto_sc.create_auto_scaling_group(
    AutoScalingGroupName = 'AppTierASG',
    LaunchTemplate = {
        'LaunchTemplateId': app_launch_template['LaunchTemplate']['LaunchTemplateId'],
        #'LaunchTemplateName': 'test'#App_tier_template',#app_launch_template['LaunchTemplate']['LaunchTemplateName']
        'Version': '$Default'
    },
    VPCZoneIdentifier = f'{private_subnet_a.id},{private_subnet_b.id}',# subnet 2 and 5 id
    TargetGroupARNs = [app_target_group['TargetGroups'][0]['TargetGroupArn']], #[app_target_group['TargetGroups'][0]['TargetGroupArn']],
    MinSize = 2,
    MaxSize = 2,
    DesiredCapacity = 2,
)



# PART 5 - Web Tier Instance Deployment

# Web Instance Deployment
ec2_create_web = ec2.create_instances(
    BlockDeviceMappings = [ 
        {
        'DeviceName': '/dev/xvda',
        'Ebs': {
            'DeleteOnTermination': True,
            'Iops': 3000,
            'VolumeSize': 8,
            'VolumeType': 'gp3',
            'Throughput': 125
            },
        },
    ],
    ImageId = 'ami-0cf10cdf9fcd62d37',
    InstanceType = 't2.micro',
    MaxCount = 1,
    MinCount = 1,
    IamInstanceProfile={
        'Name': 'ec2_role'
    },
    NetworkInterfaces = [
    {
      "SubnetId": public_subnet_a.id, #public_subnet_a.id
      "AssociatePublicIpAddress": True,
      "DeviceIndex": 0,
      "Groups": [
        web_tier_sg.id
      ]
    }
  ],
)

client.create_tags(
            Resources = [ec2_create_web[0].id],
            Tags = [
                {
                    'Key' : 'Name',
                    'Value' : 'Web Layer'
                },
            ]
        )

# Part 6
# Creating the web tier AMI
ami = client.create_image(
    BlockDeviceMappings=[
        {
            'DeviceName': '/dev/xvda',
            'Ebs': {
                'DeleteOnTermination': True,
                'VolumeSize': 8,
            },
        },   
    ],
    Description='Image of our web tier instance.',
    InstanceId = ec2_create_web[0].id,
    Name = 'Web Tier Image',
    NoReboot = True,
)


# Creating target group for the web tier
web_target_group = elb.create_target_group(
    Name = 'WebTierTagertGroup',
    Protocol = 'HTTP',
    Port = 80,
    VpcId = vpc.id, # test_1.vpc_id
    HealthCheckProtocol = 'HTTP',
    HealthCheckEnabled = True,
    HealthCheckPath = '/health',
    TargetType = 'instance'
)

print(web_target_group)

# Creating Load balancer for web tier
web_lb = elb.create_load_balancer(
    Name = 'web-tier-external-lb',
    Subnets = [public_subnet_a.id, public_subnet_b.id], #public_subnet_a.id and public_subnet_b.id
    SecurityGroups = [internet_facing_lb_sg.id], #internet_facing_lb_sg.id
    Scheme = 'internet-facing',
    Type = 'application',
    IpAddressType = 'ipv4'
)

# Creating listener to the web load balancer
web_listener = elb.create_listener(
    DefaultActions=[
        {
            'TargetGroupArn': web_target_group['TargetGroups'][0]['TargetGroupArn'], #web_target_group ARN
            'Type': 'forward',
        },
    ],
    LoadBalancerArn = web_lb['LoadBalancers'][0]['LoadBalancerArn'], #web_lb ARN
    Port=80,
    Protocol='HTTP',
)

# Creating the launch template for the web tier instance
web_launch_template = client.create_launch_template(
    LaunchTemplateName = 'Web_tier_template',
    LaunchTemplateData = {
        'ImageId': ami['ImageId'],
        'InstanceType': 't2.micro',
        'IamInstanceProfile': {
            'Arn': 'arn:aws:iam::851725412064:instance-profile/ec2_role',
            #'Name': 'ec2_role'
        },
        'SecurityGroupIds': [web_tier_sg.id], #web_tier_sg.id
        'BlockDeviceMappings':[
            {   
                'DeviceName': '/dev/xvda',
                'Ebs': {
                'VolumeSize': 8,
                'VolumeType': 'gp2',
            },
            },
        ],
    },
)

print(web_launch_template)

# Creating the web tier auto scaling group
web_auto_scaling_grp = auto_sc.create_auto_scaling_group(
    AutoScalingGroupName = 'WebTierASG',
    LaunchTemplate = {
        'LaunchTemplateId': web_launch_template['LaunchTemplate']['LaunchTemplateId'],
        #'LaunchTemplateName': 'test'#App_tier_template',#app_launch_template['LaunchTemplate']['LaunchTemplateName']
        'Version': '$Default'
    },
    VPCZoneIdentifier = f'{public_subnet_a.id},{public_subnet_b.id}',# subnet 1 and 4 id
    TargetGroupARNs = [web_target_group['TargetGroups'][0]['TargetGroupArn']],
    MinSize = 2,
    MaxSize = 2,
    DesiredCapacity = 2,
)

