import paramiko
import datetime


def main():
    # set up environmental variables
    host_name = "13.238.116.70"
    user_name = "ec2-user"
    key_path = "C:/automate/lseg_capital_markets_pem"
    service_name = "httpd"

    # get ssh client object
    ssh_connection = paramiko.SSHClient()

    # remove known host error
    ssh_connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # create connection to host
    ssh_connection.connect(
        hostname=host_name,
        username=user_name,
        key_filename=key_path
    )

    # set up bash commands in string variables
    cmd_service_status = f"systemctl is-active {service_name}"
    cmd_start_httpd = f"sudo systemctl start {service_name}"
    cmd_read_content = f"wget http://{host_name}/ -q -O -"

    # set up date/time variables
    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    date = datetime.datetime.now().strftime("%Y-%m-%d")

    # check httpd status
    httpd_status = execute(ssh_connection, cmd_service_status)

    # if httpd is not active then start the service
    if httpd_status != "active":
        execute(ssh_connection, cmd_start_httpd)

    # read web content from the hosted httpd web page
    web_content = execute(ssh_connection, cmd_read_content)

    # write to file and sync to s3
    write_log(ssh_connection, web_content, timestamp, date)

    # close ssh connection
    ssh_connection.close()


def sync_s3(connection, file_location, date):
    # location of the s3 bucket
    bucket_location = "s3://lsegcapitalmarkets/logs/"

    # command variable for s3 sync
    cmd_copy_bucket = f"aws s3 cp {file_location} {bucket_location}{date}/"
    cmd_verify_bubcket = f"aws s3 ls {bucket_location}{date}/"

    # sync file with s3
    execute(connection, cmd_copy_bucket)

    # verify if files are copied
    execute(connection, cmd_verify_bubcket)


def write_log(connection, content, timestamp, date):
    # text file location to save on local
    file_location = f"logs/{timestamp}.txt"

    # command variables for file write
    cmd_mkdir_log = "mkdir -p logs"
    cmd_write_file = f"echo '{timestamp}: {content}' > {file_location}"

    # create log folder if not exists
    execute(connection, cmd_mkdir_log)

    # write to file
    execute(connection, cmd_write_file)

    # sync file to s3
    sync_s3(connection, file_location, date)


def execute(connection, command) -> str:
    # execute script
    std_in, std_out, std_err = connection.exec_command(command)

    # result of execution from shell standard out
    result = std_out.read().decode().strip()

    # print all outputs
    print(f"{command} - {result}")

    # return result status from script
    return result


if __name__ == '__main__':
    main()