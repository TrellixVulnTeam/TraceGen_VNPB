#SynchroTraceGen

For use with [Sigil](https://github.com/dpac-vlsi/Sigil) or [Sigil2](https://github.com/mdlui/Sigil2), and [Parsec 3.0](http://parsec.cs.princeton.edu/parsec3-doc.htm).

```
git clone https://github.com/mdlui/TraceGen
cd TraceGen
SynchroTraceGen/gen_sigil_traces.py -h
```

####For Dragon Cluster users
Traditionally batch trace generation on the dragon cluster is accomplished with the HTCondor system. 
The dragon cluster is configured to allocate 1 CPU core resource for each queue slot.
For Sigil (v1) this is not a problem because the tool is single-threaded.
However, because Sigil2 is multithreaded and can regularly use >100 CPU load,
running Sigil2 manually will be more favorable until the resources are expanded.

In short, use this script or run Sigil2 manually, not in HTCondor.
