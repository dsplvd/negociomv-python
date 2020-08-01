import time
from datetime import datetime
month = datetime.now().month;
# print('%02d' % month);
completed_latest = '/home/pi/temp_files/COMPLETED/'+str(datetime.now().year)+'MO'+str('%02d' % datetime.now().month)+'.CSV';
print(completed_latest);
