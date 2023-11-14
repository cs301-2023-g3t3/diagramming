from diagrams import Diagram, Cluster, Edge

from diagrams.generic.compute import Rack
from diagrams.onprem.client import User
from diagrams.aws.network import Route53, VPCPeering
from diagrams.aws.mobile import Amplify, APIGateway
from diagrams.aws.security import Cognito, WAF, IdentityAndAccessManagementIam
from diagrams.aws.compute import Lambda
from diagrams.aws.database import Aurora
from diagrams.aws.storage import SimpleStorageServiceS3
from diagrams.aws.management import Cloudwatch
from diagrams.aws.integration import SimpleQueueServiceSqs
from diagrams.aws.engagement import SimpleEmailServiceSes
from diagrams.custom import Custom


with Diagram("Architecture Diagram", show=False, direction="TB"):
    user = User("Users")
    ext_sys = Rack("External Systems")
    with Cluster("MongoDB Atlas Cluster"):
        mongodb = Custom("MongoDB","./custom_icons/mongodbicon.png")

    with Cluster("AWS Cloud"):
        rt53 = Route53("Route 53")
        amplify = Amplify("AWS Amplify")
        with Cluster("auth"):
            cognito = Cognito("Amazon Cognito")
            auth_lambda = Lambda("AWS Lambda")

        [ext_sys,user] >> Edge(label = "Uses") >> rt53
        rt53 >> amplify >> Edge(label = "User Login") >> cognito
        
        with Cluster("AWS API Gateway"):
            with Cluster("Region (ap-southeast-1"):
                g1 = APIGateway("AWS API Gateway")


        rt53 >> Edge(label = "HTTPS Request") >> g1
        amplify >> Edge(label = "HTTPS Request") >> g1
        g1 >> Edge(label = "Verify") >> cognito

        logs = Lambda("AWS Lambda")
 
        with Cluster("Other services"):
            WAF("AWS WAF")
            Cognito("Amazon Cognito")
            Cloudwatch("Amazon Cloudwatch")
            IdentityAndAccessManagementIam("AWS IAM")
            s3 = SimpleStorageServiceS3("AWS S3")

        with Cluster("VPC"):
            with Cluster("Private Subnet"):
                with Cluster("User Storage"):
                    with Cluster("Rest API"):
                        user_storage = Lambda("AWS Lambda")
            
                with Cluster("Points Ledger"):
                    with Cluster("Rest API"):
                        points_ledger = Lambda("AWS Lambda")
            
                with Cluster("MakerChecker"):
                    with Cluster("Rest API"):
                        maker_checker = Lambda("AWS Lambda")

                with Cluster("Primary Database"):
                    pri_DB = Aurora("Amazon Aurora")
            
                with Cluster("Read Replica"):
                    rr = Aurora("Amazon Aurora")
            
                pri_DB >> Edge(label = "Synchronize") >> rr
                vpcpc = VPCPeering("VPC Peering Connection")

        g1 >> Edge(label = "Forward Requests") >> [user_storage,points_ledger,maker_checker]
        g1 >> Edge(label = "Query Logs") >> logs >> Edge(label = "Fetch Logs") >> s3

        cognito >> rr
        maker_checker >> Edge(label = "Maker Requests Approved") >> [points_ledger, user_storage]
        maker_checker >> vpcpc >> mongodb

        points_ledger >> Edge(label = "Read DB") >> [pri_DB, rr]
        user_storage >> Edge(label = "Write DB") >> [pri_DB, rr]

        sqs = SimpleQueueServiceSqs("AWS SQS")
        maker_checker >> Edge(label = "Create Message") >> sqs
        sqs >> Edge(label = "Timeout Messages") >> SimpleQueueServiceSqs("DLQ")
        user << Edge(label = "Sends Email") << SimpleEmailServiceSes("AWS SES") << Edge(label = "Create Email") << Lambda("AWS Lambda") <<  Edge(label = "Poll Message") << sqs
