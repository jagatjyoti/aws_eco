# aws_eco

Cost optimizer for your Kubernetes Cluster on AWS

## Things to consider

This project helps you reduce costs for your self hosted Kubernetes cluster on AWS. It can be run to power-on or power-off instances in a particular order Kubernetes is fond of. Make sure your instances' tags look exactly like below:

![ec2](https://user-images.githubusercontent.com/17386913/57473641-e5186280-72ad-11e9-942a-848881fa8817.JPG)

## Getting it running

Just run the script ```setup_venv.sh``` to setup the virtual environment and install necessary packages. For now it can be run on CentOS only (although aws_eco can run on Python 3).

Also, set AWS_SECRET_KEY and SECRET_ACCESS_KEY as environment variables before hand.

## Usage

```./aws_eco control_environment [start/stop] jjm us-east-1 ```

## Sample output

![moba](https://user-images.githubusercontent.com/17386913/57473714-1b55e200-72ae-11e9-98b5-12394417466e.JPG)

## Special notes

To be added ... 
