import os
import boto3
import datetime
import shutil
import glob
import tarfile
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def main():
    logging.info("starting log archival")

    # current date
    current_date = "2021-02-17"# datetime.datetime.now().strftime("%Y-%m-%d")

    logging.info(f"current date set to {current_date}")

    # s3 variables setup
    resource_name = "s3"
    bucket_name = f"lsegcapitalmarkets"
    archive_url = f"logs_archive/{current_date}"

    # artifact variables setup
    logs_dir = "logs_raw"
    dir_tree = f"{logs_dir}/{current_date}"
    artifact_name = f"{current_date}.tar.gz"

    # mailing variables setup
    username = "vishkanr@gmail.com"
    password = "Civic1999"
    recipient = "vishkanraj@yahoo.com"
    subject = "FAILURE - Logging archive process failed"
    body = f"The log archival process has failed on {current_date} due to "

    logging.info("initialized all required variables")

    # get s3 bucket
    s3 = boto3.resource(resource_name)
    bucket = s3.Bucket(bucket_name)

    logging.info("creating local directories")

    # if local path doesnt exist create it
    if not os.path.exists(dir_tree):
        os.makedirs(dir_tree)

    # keep count of downloaded files
    downloaded_count = 0

    logging.info("downloading files from s3 bucket")

    # iterate all keys
    for obj in bucket.objects.all():
        # filename to download taken from the key
        filename = str(obj.key.rsplit('/')[-1]).replace(':', '')

        # download only what is available for specified date
        if current_date in filename:
            bucket.download_file(obj.key, f"{dir_tree}/{filename}")
            downloaded_count += 1

    # if download count is greater than 0 upload to s3, else send email to support team
    if downloaded_count > 0:
        logging.info("downloading from s3 successful")

        # create tar artifact from all files downloaded
        create_artifact(dir_tree, "txt", artifact_name)

        logging.info("uploading tar archive to s3")

        # upload zip artifact to s3 bucket
        s3.meta.client.upload_file(artifact_name, bucket_name, f"{archive_url}/{artifact_name}")

        logging.info("cleaning directories")

        # remove tar file
        os.remove(f"{artifact_name}")

        # remove raw logs
        shutil.rmtree(logs_dir)
    else:
        logging.info("downloading files from s3 failed")

        # update error
        body += "no files being downloaded for set date. Please verify urgently!"

        logging.info("sending email to support team")

        # send email
        generate_email(username, password, recipient, subject, body)

    logging.info("completed log archival execution")


def create_artifact(source_dir, file_extension, artifact_name):
    # open tar creation
    tar = tarfile.open(artifact_name, "w:gz")

    # iterate through source destination looking for specified file extension
    for path in glob.glob(f"{source_dir}/*.{file_extension}"):
        tar.add(path)

    # close tar creation
    tar.close()


def generate_email(username, password, recipient, subject, body):
    # Setup email as multipart MIME
    mail = MIMEMultipart()

    # set email structure
    mail['From'] = username
    mail['To'] = recipient
    mail['Subject'] = subject
    mail.attach(MIMEText(body, 'plain'))

    # setup SMTP session with gmail port and enable security options
    session = smtplib.SMTP('smtp.gmail.com', 587)
    session.starttls()

    # login to email account and send email
    session.login(username, password)
    text = mail.as_string()
    session.sendmail(username, recipient, text)

    # close smtp session
    session.quit()


if __name__ == '__main__':
    # set logging level to info
    logging.basicConfig(level=logging.INFO)

    # start main execution
    main()