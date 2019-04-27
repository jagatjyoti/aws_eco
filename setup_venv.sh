#!/bin/bash

#Error handling function
function run() {
  cmd_output=$(eval $1)
  return_value=$?
  if [ $return_value != 0 ]; then
    echo "$cmd_output"
    echo "Command $1 failed"
    exit -1
  else
    echo "[OK]"
  fi
  return $return_value
}

#Setup virtual environment
function setup_venv()
{
  DIRECTORY="venv"
  echo "- Installing python 3.6" && run "yum install -y python36u > /dev/null"
  echo "- Verifying Installation" && run "python3.6 -V"
  echo "- Installing pip 3.6" && run "yum -y install python-pip"
  echo "- Installing virtualenv" && run "pip3 install --upgrade pip && pip3 install -U virtualenv"
  if [ ! -d "$DIRECTORY" ]; then
    echo "- Creating directory venv" && run "mkdir $DIRECTORY"
  fi
  echo "- Setting up virtual environment"
  run "virtualenv -p python3 $DIRECTORY &&  source $DIRECTORY/bin/activate && pip3 install -U boto3 &&  which python"
  echo "- Virtual environment setup successfully. Run \"source $DIRECTORY/bin/activate\" to access it."
}

#Main
setup_venv
