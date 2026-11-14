import sys,time
sys.path.insert(0, __import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)), '..', '..', 'tests'))
from lib.c64 import Vice
d='/tmp/claude-0/proto/t2.d64'
drv=sys.argv[1] if len(sys.argv)>1 else '1541'
v=Vice(d,boot_wait=0.5,extra=["-autostart",d,"-drive8type",drv] if drv!='1541' else ["-autostart",d])
time.sleep(25)
print("pre-save s1,s8 status",hex(v.b(0xc030)),hex(v.b(0xc031)))
print("mark",hex(v.b(0xc0ff)))
print("install A,C",v.b(0xc000),v.b(0xc001),"codes",[hex(v.b(0xc000+i)) for i in range(2,9)],"save C",v.b(0xc015),v.b(0xc016))
s=v.mem(0xc020,40)
t=[s[i]*0+ (s[i+0]+256*s[i+1]) for i in range(0,40,4)]
# counters count down: ticks = (TB:TA) value
vals=[ (0xffffffff-((s[i+3]<<24)|(s[i+2]<<16)|(s[i+1]<<8)|s[i])) for i in range(0,40,4)]
names=["start","install","data1622B","hi2018B","savePlugin","save1","save8","save1b","read s1","read s8"]
for i in range(1,10): print("%-12s %8.3f s"%(names[i], (vals[i]-vals[i-1])/985248.0))
v.close()
