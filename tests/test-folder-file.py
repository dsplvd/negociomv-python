import os

def file_get_contents(filename):
  if os.path.exists(filename):
    fp = open(filename, "r")
    content = fp.read()
    fp.close()
    return content


homePath = os.path.expanduser("~")
completeFolder = file_get_contents(homePath + '/completed-folder')
print "COMPLETED FOLDER"
print completeFolder
ticketFolder = file_get_contents(homePath + '/ticket-folder')
print "TICKET FOLDER"
print ticketFolder
