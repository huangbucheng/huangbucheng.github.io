# Jmeter Distributed Testing
https://jmeter.apache.org/usermanual/jmeter_distributed_testing_step_by_step.html

[Err] 
```
Created remote object: UnicastServerRef2 [liveRef: [endpoint:[127.0.0.1:34671](local),objID:[3bbdcabd:19203f26b5c:-7fff, -2681917709249863073]]]
Server failed to start: java.rmi.RemoteException: Cannot start. VM-1-173-centos is a loopback address.
An error occurred: Cannot start. VM-1-173-centos is a loopback address.
```

solution:
```
./jmeter-server -Djava.rmi.server.hostname=xxx.xxx.xxx.xxx
```
Replace xxx.xxx.xxx.xxx with this server's IP address, i.e., the IP address that the controlling jmeter machine will use to connect to this server.
